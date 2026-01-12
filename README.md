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
| **LLM** | Groq (Llama-3.3-70b) |
| **Embeddings** | Mistral (mistral-embed) |
| **Reranking** | Cohere |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/cvignesh/Legal_Assistant.git
cd Legal_Assistant

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run Backend
uvicorn app.main:app --reload

# Run Frontend
cd frontend && npm install && npm run dev
```

---

## 📁 Project Structure

```
Legal_Assistant/
├── app/
│   ├── api/           # FastAPI routes
│   ├── parser/        # Smart Parser (Narrative/Strict/Schedule)
│   ├── services/      # Retriever, LLM, Database
│   └── models/        # Pydantic schemas
├── frontend/          # React + Material UI
├── scripts/           # Batch ingestion CLI
├── tests/             # Unit & integration tests
├── docs/              # UI mockups & diagrams
└── DESIGN.md          # Full implementation plan
```

---

## 📖 Documentation

- **[Full Design Document](DESIGN.md)** - Detailed implementation plan
- **[UI Mockups](docs/)** - Interface prototypes

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