# Backend Testing Guide

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your API keys (GROQ, Mistral, MongoDB URI)

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
# API tests only
pytest backend/tests/api/test_ingestion.py

# Parser tests only
pytest backend/tests/services/test_parser.py
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test
```bash
pytest backend/tests/api/test_ingestion.py::test_health_check
```

## Test Coverage

| Module | Tests | Description |
|:---|:---:|:---|
| **API - Ingestion** | 7 | Upload, Status, Preview, Confirm, Error Handling |
| **Services - Parser** | 4 | PDF Processing, Error Cases, Chunk Structure |

## Notes

- **Sample PDFs Required**: Tests expect `Sample_pdf/BNS.pdf` to exist
- **MongoDB Connection**: Tests use the actual MongoDB from `.env` (not mocked)
- **Confirm Endpoint**: Skipped in tests to avoid DB pollution

## Expected Results

```
========== test session starts ==========
backend/tests/api/test_ingestion.py ✓✓✓✓✓✓✓
backend/tests/services/test_parser.py ✓✓✓✓

========== 11 passed in 12.34s ==========
```
