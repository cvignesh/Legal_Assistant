# Legal Assistant

An AI-powered assistant for **Indian Laws, Acts & Case Law (Judgments)** built with RAG (Retrieval-Augmented Generation).
---

## 🎯 Features

### 📚 Document Ingestion
- **Batch PDF Upload** - CLI and UI-based ingestion
- **Smart Parser** - Auto-detects document type (Narrative, Strict, Schedule modes)
- **Vision OCR** - Handles scanned PDFs using Llama Vision
- **Real-time Progress** - Live status tracking with retry on failure

### 🔍 Search
- **Hybrid Search** - Vector + BM25 keyword search
- **Autocomplete** - Suggest acts/sections as you type
- **Filters** - By Act, Category, Court, Year
- **Cross-References** - See related sections across acts

### 💬 Legal Chat
- **Natural Language Q&A** - Ask questions in English/Hindi
- **Source Citations** - Clickable chips showing exact sections
- **Conversation Memory** - Context-aware multi-turn chat
- **Hallucination Prevention** - Refuses to answer without sufficient context

### ⚖️ Viability Predictor
- **Case Outcome Prediction** - Predict if petition will be Allowed/Dismissed
- **Confidence Score** - High/Medium/Low viability
- **Supporting Cases** - Similar past judgments

### 🧠 Argument Miner
- **Extract Legal Arguments** - Prosecution vs Defense
- **Winning Strategy** - Highlight successful arguments
- **Source Citations** - Direct links to judgment text

### 📝 Clause Search
- **Legal Phrasing Search** - Find exact petition language
- **Quoted Text** - Copy-ready exact quotes with source
- **Multiple Suggestions** - Alternative phrasings

---

## 📊 Data Sources

| Type | Source | Volume |
|:---|:---|:---|
| **Laws/Acts** | India Code, MHA Gazette | BNS, BNSS, BSA, IPC, CrPC + more |
| **Judgments (POC)** | [HuggingFace InJudgements](https://huggingface.co/datasets/opennyaiorg/InJudgements_dataset) | 10,000 cases |
| **Judgments (Prod)** | [Indian Kanoon](https://indiankanoon.org/) | All courts |

---

## 🛠️ Tech Stack

| Component | Technology |
|:---|:---|
| **Backend** | Python, FastAPI, LangChain |
| **Frontend** | React, Vite, Material UI |
| **Database** | MongoDB Atlas (Vector + Text Search) |
| **LLM** | Groq (Llama-3.3-70b, Llama-3.1-8b-instant) |
| **Embeddings** | Mistral (mistral-embed, 1024-dim) |
| **Reranking** | Cohere |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **MongoDB Atlas** account
- **API Keys**: Groq, Mistral, Cohere

### 1. Clone Repository

```bash
git clone https://github.com/cvignesh/Legal_Assistant.git
cd Legal_Assistant
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv RAGLegalAssistant

# Activate virtual environment
# Windows PowerShell:
.\RAGLegalAssistant\Scripts\Activate.ps1

# Linux/Mac:
source RAGLegalAssistant/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example env file (if available)
cp .env.example .env

# Or create .env manually with required keys
```

**Required API Keys in `.env`:**
```env
# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB=legal_db
MONGO_COLLECTION_CHUNKS=legal_chunks_v1

# LLM (Groq)
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile

# Embeddings (Mistral)
MISTRAL_API_KEY=your_mistral_api_key
EMBED_MODEL=mistral-embed

# Reranking (Cohere)
COHERE_API_KEY=your_cohere_api_key
```

### 4. Start Backend Server

```bash
# From backend directory (with venv activated)
uvicorn app.main:app --reload
```

**Server will start at:** `http://localhost:8000`

**Verify:** http://localhost:8000/docs (FastAPI Swagger UI)

---

## 📥 Data Ingestion

### Ingest Judgment PDFs (CLI Batch Script)

**Process Multiple Judgments Automatically:**

```bash
# From backend directory (with server running in another terminal)
python scripts/ingest_judgments_batch.py --folder /path/to/judgment/pdfs/
```

**Example with POC Judgments:**

```bash
python scripts/ingest_judgments_batch.py --folder ../_legacy_poc/Judgment_parsing_POC/
```

**CLI Options:**

| Option | Description |
|--------|-------------|
| `--folder PATH` | Path to folder containing judgment PDFs (required) |
| `--no-auto-confirm` | Don't auto-confirm jobs (manual review required) |
| `--help` | Show help message |

**Processing Output:**

```
======================================================================
   Judgment PDF Batch Ingestion Tool
======================================================================

Found 3 PDF file(s)
Auto-confirm: Yes

[1/3]
📄 Processing: judgment1.pdf
  → Uploading...
    ✓ Uploaded (Job ID: abc12345...)
  → Waiting for parsing...
    ⚡ Parsing in progress...
    ✓ Parsing completed!
  → Confirming & starting indexing...
    ✓ Completed! 396 chunks indexed

====================================================================== 
  📊 SUMMARY REPORT
======================================================================

  ✓ Completed: 3
  Total Chunks Indexed: 1,250
  Total Processing Time: 22.5 minutes
======================================================================
```

**Processing Time:** ~6-7 minutes per 50-page judgment (LLM rate limits)

---

### Ingest ACT PDFs (API Method)

> **Note:** ACT CLI batch script coming soon. Currently use API via Swagger UI.

**Via FastAPI Swagger UI:**
1. Go to http://localhost:8000/docs
2. Find `POST /api/ingest/upload`
3. Upload ACT PDF files
4. Monitor: `GET /api/ingest/{job_id}/status`
5. Confirm: `POST /api/ingest/{job_id}/confirm`


---

## 🖥️ Frontend Setup

**Navigate to frontend directory:**

```bash
cd frontend
```

**Install dependencies:**

```bash
npm install
```

**Configure API endpoint (Optional):**

The frontend is pre-configured to proxy API requests to `http://localhost:8000`. If your backend runs on a different port, update `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:YOUR_PORT'
  }
}
```

**Start development server:**

```bash
npm run dev
```

**Frontend will start at:** `http://localhost:5173`

**Available Features:**
- 📁 **Document Upload** - Upload acts/laws and judgment PDFs with real-time progress tracking
- 🔍 **Hybrid Search** - Search across all indexed legal documents
- 💬 **Legal Chat** - Ask questions and get answers with source citations
- ⚖️ **Case Analysis** - Viability prediction, argument mining, and clause search

**Build for production:**

```bash
npm run build
```

**Preview production build:**

```bash
npm run preview
```

---

## 📁 Project Structure

```
Legal_Assistant/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   │   └── routes/
│   │   │       ├── ingestion.py      # ACT PDF ingestion
│   │   │       └── judgments.py      # Judgment PDF ingestion
│   │   ├── services/
│   │   │   ├── parser/       # ACT PDF parser
│   │   │   ├── judgment/     # Judgment PDF parser with LLM
│   │   │   ├── embedder.py   # Mistral embeddings
│   │   │   └── ingestion.py  # Ingestion orchestration
│   │   └── core/
│   │       └── config.py     # Environment configuration
│   ├── scripts/
│   │   └── ingest_judgments_batch.py    # CLI batch tool
│   ├── data/
│   │   └── judgments/        # Processed JSON outputs (gitignored)
│   └── tests/
├── frontend/                  # React + Material UI
├── _legacy_poc/              # POC scripts and sample data
├── DESIGN.md                 # Full implementation plan
└── README.md                 # This file
```

---

## 📖 Documentation

- **[Full Design Document](DESIGN.md)** - Comprehensive implementation details
  - Judgment Processing Architecture
  - Manual Testing Guide
  - CLI Batch Processing Guide
  - Use Case Metadata Mapping
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when server is running)

---

## 🔒 Security Features

- **PII Handling** - Dual storage (original + sanitized)
- **Sensitive Case Detection** - Auto-flag POCSO/Juvenile cases
- **Access Control** - Role-based permissions
- **Audit Trail** - Log all sensitive data access

---

## 📈 Quality Metrics (DeepEval)

| Metric | Target |
|:---|:---:|
| Faithfulness | ≥ 0.9 |
| Answer Relevancy | ≥ 0.85 |
| Hallucination Rate | ≤ 0.1 |

---

## 🧪 Testing

**Manual API Testing:**
Refer to DESIGN.md "Manual Testing Guide for Judgment APIs" section for step-by-step commands.

**Integration Tests:**
```bash
cd backend
pytest tests/api/test_judgment_integration.py -v
```

---

## 🤝 Contributing

See [DESIGN.md](DESIGN.md) for detailed architecture and implementation guidelines.

---

## 📄 License

This project is for educational and research purposes.