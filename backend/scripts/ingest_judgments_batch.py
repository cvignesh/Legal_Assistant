"""
CLI Batch Ingestion Script for Judgment PDFs

Usage:
    python scripts/ingest_judgments_batch.py --folder ./path/to/judgments/
    
Features:
- Scans folder for all PDF files
- Uploads each to judgment API
- Monitors parsing progress
- Waits for completion
- Shows progress and summary report
"""
import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# API Configuration
API_BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/judgments/upload"
STATUS_ENDPOINT = f"{API_BASE_URL}/api/judgments/{{job_id}}/status"
CONFIRM_ENDPOINT = f"{API_BASE_URL}/api/judgments/{{job_id}}/confirm"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print script banner"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"{Colors.BLUE}   Judgment PDF Batch Ingestion Tool{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")


def find_pdfs(folder_path: Path) -> List[Path]:
    """Find all PDF files in the given folder"""
    # Use set logic on resolved paths to avoid duplicates on Windows
    pdfs = set()
    for p in folder_path.glob("*.PDF"):
        pdfs.add(p.resolve())
    for p in folder_path.glob("*.pdf"):
        pdfs.add(p.resolve())
    return sorted(list(pdfs))


def upload_judgment(pdf_path: Path) -> Dict:
    """Upload a judgment PDF to the API"""
    try:
        with open(pdf_path, 'rb') as f:
            files = {'files': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=30)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_job_status(job_id: str) -> Dict:
    """Get status of a judgment processing job"""
    response = None
    try:
        url = STATUS_ENDPOINT.format(job_id=job_id)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = response.status_code if response else "N/A"
        return {"error": f"HTTP {status_code}: {str(e)}"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection failed: Cannot reach server at {API_BASE_URL}"}
    except requests.exceptions.Timeout as e:
        return {"error": f"Request timeout after 10s"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


def confirm_job(job_id: str) -> Dict:
    """Confirm a job to start indexing"""
    try:
        response = requests.post(CONFIRM_ENDPOINT.format(job_id=job_id), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def wait_for_parsing(job_id: str, filename: str, timeout: int = 3600) -> bool:
    """Wait for parsing to complete (max 60 minutes)"""
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status_data = get_job_status(job_id)
        
        # Check for actual errors (not None)
        if status_data.get("error"):
            print(f"    {Colors.RED}✗ Error checking status: {status_data['error']}{Colors.RESET}")
            return False
        
        status = status_data.get("status")
        
        # Print status changes
        if status != last_status:
            if status == "parsing":
                print(f"    {Colors.YELLOW}⚡ Parsing in progress...{Colors.RESET}")
            elif status == "preview_ready":
                print(f"    {Colors.GREEN}✓ Parsing completed!{Colors.RESET}")
                return True
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"    {Colors.RED}✗ Parsing failed: {error}{Colors.RESET}")
                return False
            last_status = status
        
        time.sleep(5)  # Check every 5 seconds
    
    print(f"    {Colors.RED}✗ Timeout waiting for parsing{Colors.RESET}")
    return False


def wait_for_indexing(job_id: str, timeout: int = 300) -> bool:
    """Wait for indexing to complete (max 5 minutes)"""
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status_data = get_job_status(job_id)
        
        if status_data.get("error"):
            print(f"    {Colors.RED}✗ Error checking status: {status_data['error']}{Colors.RESET}")
            return False
        
        status = status_data.get("status")
        
        if status != last_status:
            if status == "indexing":
                print(f"    {Colors.YELLOW}📊 Indexing to MongoDB...{Colors.RESET}")
            elif status == "completed":
                summary = status_data.get("summary", {})
                print(f"    {Colors.GREEN}✓ Completed! {summary.get('total_chunks', 0)} chunks indexed{Colors.RESET}")
                return True
            elif status == "failed":
                print(f"    {Colors.RED}✗ Indexing failed{Colors.RESET}")
                return False
            last_status = status
        
        time.sleep(3)
    
    print(f"    {Colors.RED}✗ Timeout waiting for indexing{Colors.RESET}")
    return False


def process_judgment(pdf_path: Path, auto_confirm: bool = True) -> Dict:
    """Process a single judgment PDF end-to-end"""
    result = {
        "filename": pdf_path.name,
        "status": "pending",
        "job_id": None,
        "chunks": 0,
        "error": None
    }
    
    print(f"\n{Colors.BOLD}📄 Processing: {pdf_path.name}{Colors.RESET}")
    
    # Step 1: Upload
    print(f"  {Colors.BLUE}→ Uploading...{Colors.RESET}")
    upload_response = upload_judgment(pdf_path)
    
    if "error" in upload_response:
        result["status"] = "failed"
        result["error"] = upload_response["error"]
        print(f"    {Colors.RED}✗ Upload failed: {upload_response['error']}{Colors.RESET}")
        return result
    
    # Check for per-file errors in response
    if not upload_response.get("jobs"):
        result["status"] = "failed"
        result["error"] = "No job created by API"
        print(f"    {Colors.RED}✗ Upload failed: No job returned{Colors.RESET}")
        return result
        
    job_data = upload_response["jobs"][0]
    if job_data.get("status") == "failed":
        result["status"] = "failed"
        result["error"] = job_data.get("error", "Unknown upload error")
        print(f"    {Colors.RED}✗ Upload failed: {result['error']}{Colors.RESET}")
        return result
        
    job_id = job_data["job_id"]
    result["job_id"] = job_id
    print(f"    {Colors.GREEN}✓ Uploaded (Job ID: {job_id[:8]}...){Colors.RESET}")
    
    # Step 2: Wait for parsing
    print(f"  {Colors.BLUE}→ Waiting for parsing...{Colors.RESET}")
    if not wait_for_parsing(job_id, pdf_path.name):
        result["status"] = "parsing_failed"
        return result
    
    # Step 3: Auto-confirm (or manual)
    if auto_confirm:
        print(f"  {Colors.BLUE}→ Confirming & starting indexing...{Colors.RESET}")
        confirm_response = confirm_job(job_id)
        
        if "error" in confirm_response:
            result["status"] = "confirm_failed"
            result["error"] = confirm_response["error"]
            return result
        
        # Step 4: Wait for indexing
        if wait_for_indexing(job_id):
            # Get final status
            final_status = get_job_status(job_id)
            result["status"] = "completed"
            result["chunks"] = final_status.get("summary", {}).get("total_chunks", 0)
        else:
            result["status"] = "indexing_failed"
    else:
        result["status"] = "preview_ready"
        print(f"    {Colors.YELLOW}⚠ Manual confirmation required{Colors.RESET}")
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Batch process judgment PDFs for ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ingest_judgments_batch.py --folder ./judgments/
  python scripts/ingest_judgments_batch.py --folder ./judgments/ --no-auto-confirm
        """
    )
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Path to folder containing judgment PDFs"
    )
    parser.add_argument(
        "--no-auto-confirm",
        action="store_true",
        help="Don't auto-confirm jobs (requires manual confirmation via API)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Validate folder
    folder_path = Path(args.folder)
    if not folder_path.exists():
        print(f"{Colors.RED}Error: Folder not found: {folder_path}{Colors.RESET}")
        sys.exit(1)
    
    # Find PDFs
    pdfs = find_pdfs(folder_path)
    if not pdfs:
        print(f"{Colors.YELLOW}No PDF files found in {folder_path}{Colors.RESET}")
        sys.exit(0)
    
    print(f"{Colors.BOLD}Found {len(pdfs)} PDF file(s){Colors.RESET}")
    print(f"Auto-confirm: {Colors.GREEN if not args.no_auto_confirm else Colors.YELLOW}{'Yes' if not args.no_auto_confirm else 'No'}{Colors.RESET}\n")
    
    # Process each PDF
    results = []
    start_time = datetime.now()
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"\n{Colors.BOLD}[{i}/{len(pdfs)}]{Colors.RESET}")
        result = process_judgment(pdf, auto_confirm=not args.no_auto_confirm)
        results.append(result)
        
        # Brief pause between files
        if i < len(pdfs):
            time.sleep(2)
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"  📊 SUMMARY REPORT")
    print(f"{'='*70}{Colors.RESET}\n")
    
    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] != "completed" and r["status"] != "preview_ready"]
    pending = [r for r in results if r["status"] == "preview_ready"]
    
    print(f"  {Colors.GREEN}✓ Completed: {len(completed)}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠ Pending Confirmation: {len(pending)}{Colors.RESET}")
    print(f"  {Colors.RED}✗ Failed: {len(failed)}{Colors.RESET}")
    print(f"  Total Processing Time: {duration:.1f}s\n")
    
    if completed:
        total_chunks = sum(r["chunks"] for r in completed)
        print(f"  {Colors.BOLD}Total Chunks Indexed: {total_chunks}{Colors.RESET}\n")
    
    if failed:
        print(f"\n{Colors.RED}Failed Files:{Colors.RESET}")
        for r in failed:
            print(f"  - {r['filename']}: {r.get('error', r['status'])}")
    
    if pending:
        print(f"\n{Colors.YELLOW}Pending Confirmation:{Colors.RESET}")
        for r in pending:
            print(f"  - {r['filename']} (Job ID: {r['job_id']})")
        print(f"\n  Use API to confirm: POST /api/judgments/{{job_id}}/confirm")
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}\n")


if __name__ == "__main__":
    main()
