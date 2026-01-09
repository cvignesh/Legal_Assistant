# Legal Assistant - Complete Technology Stack

> **Last Updated**: January 9, 2026  
> **Project**: AI-Powered Legal Research & Petition Drafting Platform

---

## 🎯 System Overview

A production-grade RAG-based legal assistant for Indian laws featuring:
- Smart PDF parsing with 3 strategies (Narrative, Strict, Schedule)
- Hybrid search (Vector + BM25) with reranking
- 6 specialized features: Ingestion, Search, Chat, Viability, Arguments, Clauses
- Dual knowledge base: Statutory laws + Judicial precedents

---

## 📚 Complete Technology Stack

### **Backend Stack**

#### Core Framework
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Python** | 3.10+ | Primary language | [python.org](https://python.org) |
| **FastAPI** | 0.104+ | REST API framework | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| **Uvicorn** | 0.24+ | ASGI server | [uvicorn.org](https://www.uvicorn.org) |
| **Pydantic** | 2.5+ | Data validation | [docs.pydantic.dev](https://docs.pydantic.dev) |

#### Database & Storage
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **MongoDB Atlas** | 7.0+ | Vector + Document DB | [mongodb.com/atlas](https://www.mongodb.com/atlas) |
| **Motor** | 3.3+ | Async MongoDB driver | [motor.readthedocs.io](https://motor.readthedocs.io) |
| **Redis** | 7.0+ | Caching & task queue | [redis.io](https://redis.io) |

#### AI & Machine Learning
| Technology | Provider | Model | Purpose |
|------------|----------|-------|---------|
| **LLM** | Groq | Llama-3.3-70b-versatile | Chat generation, Q&A |
| **Embeddings** | Mistral AI | mistral-embed (1024-dim) | Vector embeddings |
| **Reranking** | Cohere | rerank-english-v3.0 | Search result refinement |
| **Vision OCR** | Groq | Llama-3.2-11b-vision-preview | Scanned PDF text extraction |

#### RAG & LLM Orchestration
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **LangChain** | 0.1+ | RAG pipeline | [python.langchain.com](https://python.langchain.com) |
| **LangChain-Groq** | Latest | Groq integration | [pypi.org/project/langchain-groq](https://pypi.org/project/langchain-groq) |
| **LangChain-MongoDB** | 0.1+ | MongoDB memory | [pypi.org/project/langchain-mongodb](https://pypi.org/project/langchain-mongodb) |

#### PDF Processing
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **pdfplumber** | 0.10+ | Text extraction | [github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber) |
| **Pillow** | 10.2+ | Image processing | [pillow.readthedocs.io](https://pillow.readthedocs.io) |
| **pdf2image** | 1.16+ | PDF to image conversion | [pypi.org/project/pdf2image](https://pypi.org/project/pdf2image) |

#### Task Queue & Background Jobs
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Celery** | 5.3+ | Async task queue | [docs.celeryq.dev](https://docs.celeryq.dev) |
| **Redis** | 7.0+ | Celery broker | [redis.io](https://redis.io) |

#### Utilities & Helpers
| Technology | Version | Purpose |
|------------|---------|---------|
| **python-dotenv** | 1.0+ | Environment config |
| **httpx** | 0.26+ | Async HTTP client |
| **tqdm** | 4.66+ | Progress bars |
| **python-multipart** | 0.0.6+ | File upload handling |

---

### **Frontend Stack**

#### Core Framework
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **React** | 18.2+ | UI framework | [react.dev](https://react.dev) |
| **Vite** | 5.0+ | Build tool & dev server | [vitejs.dev](https://vitejs.dev) |
| **JavaScript/TypeScript** | ES2022+ | Primary language | [typescriptlang.org](https://www.typescriptlang.org) |

#### UI Components & Styling
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Material UI (MUI)** | 5.15+ | Component library | [mui.com](https://mui.com) |
| **@mui/icons-material** | 5.15+ | Icon library | [mui.com/components/icons](https://mui.com/components/icons) |
| **@emotion/react** | 11.11+ | CSS-in-JS (MUI dependency) | [emotion.sh](https://emotion.sh) |
| **@emotion/styled** | 11.11+ | Styled components | [emotion.sh](https://emotion.sh) |

#### State Management & Data Fetching
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Zustand** | 4.4+ | Global state management | [github.com/pmndrs/zustand](https://github.com/pmndrs/zustand) |
| **TanStack Query** | 5.17+ | Server state & caching | [tanstack.com/query](https://tanstack.com/query) |
| **Axios** | 1.6+ | HTTP client | [axios-http.com](https://axios-http.com) |

#### Form Handling & Validation
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **React Hook Form** | 7.49+ | Form management | [react-hook-form.com](https://react-hook-form.com) |
| **Zod** | 3.22+ | Schema validation | [zod.dev](https://zod.dev) |

#### File Handling & UI Enhancements
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **react-dropzone** | 14.2+ | Drag-drop file upload | [react-dropzone.js.org](https://react-dropzone.js.org) |
| **react-pdf** | 7.6+ | PDF preview | [github.com/wojtekmaj/react-pdf](https://github.com/wojtekmaj/react-pdf) |
| **react-markdown** | 9.0+ | Markdown rendering | [github.com/remarkjs/react-markdown](https://github.com/remarkjs/react-markdown) |
| **react-hot-toast** | 2.4+ | Notifications | [react-hot-toast.com](https://react-hot-toast.com) |
| **react-copy-to-clipboard** | 5.1+ | Copy functionality | [github.com/nkbt/react-copy-to-clipboard](https://github.com/nkbt/react-copy-to-clipboard) |

#### Routing
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **React Router** | 6.21+ | Client-side routing | [reactrouter.com](https://reactrouter.com) |

---

### **DevOps & Infrastructure**

#### Containerization
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Docker** | 24.0+ | Containerization | [docker.com](https://www.docker.com) |
| **Docker Compose** | 2.23+ | Multi-container orchestration | [docs.docker.com/compose](https://docs.docker.com/compose) |

#### CI/CD
| Technology | Purpose | Documentation |
|------------|---------|---------------|
| **GitHub Actions** | Automated testing & deployment | [docs.github.com/actions](https://docs.github.com/actions) |

#### Testing
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **pytest** | 7.4+ | Python unit/integration tests | [pytest.org](https://pytest.org) |
| **pytest-asyncio** | 0.23+ | Async test support | [pypi.org/project/pytest-asyncio](https://pypi.org/project/pytest-asyncio) |
| **httpx** | 0.26+ | API testing | [www.python-httpx.org](https://www.python-httpx.org) |
| **Vitest** | 1.1+ | Frontend unit tests | [vitest.dev](https://vitest.dev) |
| **Testing Library** | 14.1+ | React component tests | [testing-library.com](https://testing-library.com) |
| **Playwright** | 1.40+ | E2E testing | [playwright.dev](https://playwright.dev) |

#### Code Quality
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **Ruff** | 0.1+ | Python linter & formatter | [docs.astral.sh/ruff](https://docs.astral.sh/ruff) |
| **Black** | 23.12+ | Python code formatter | [black.readthedocs.io](https://black.readthedocs.io) |
| **isort** | 5.13+ | Import sorting | [pycqa.github.io/isort](https://pycqa.github.io/isort) |
| **ESLint** | 8.56+ | JavaScript linter | [eslint.org](https://eslint.org) |
| **Prettier** | 3.1+ | Code formatter | [prettier.io](https://prettier.io) |
| **pre-commit** | 3.6+ | Git hooks | [pre-commit.com](https://pre-commit.com) |

#### Monitoring & Observability
| Technology | Purpose | Documentation |
|------------|---------|---------------|
| **Sentry** | Error tracking | [sentry.io](https://sentry.io) |
| **Prometheus** | Metrics collection | [prometheus.io](https://prometheus.io) |
| **Grafana** | Metrics visualization | [grafana.com](https://grafana.com) |

#### Security & Rate Limiting
| Technology | Version | Purpose | Documentation |
|------------|---------|---------|---------------|
| **slowapi** | 0.1+ | Rate limiting | [github.com/laurentS/slowapi](https://github.com/laurentS/slowapi) |
| **python-jose** | 3.3+ | JWT handling | [github.com/mpdavis/python-jose](https://github.com/mpdavis/python-jose) |

---

## 🔌 External Services & APIs

### AI/ML Services
| Service | Provider | Model/API | Cost Model |
|---------|----------|-----------|------------|
| **LLM** | Groq | Llama-3.3-70b-versatile | Pay-per-token |
| **Vision** | Groq | Llama-3.2-11b-vision-preview | Pay-per-image |
| **Embeddings** | Mistral AI | mistral-embed | Pay-per-request |
| **Reranking** | Cohere | rerank-english-v3.0 | Pay-per-request |

### Database & Storage
| Service | Provider | Tier | Purpose |
|---------|----------|------|---------|
| **MongoDB Atlas** | MongoDB | M10+ | Vector DB + Document store |
| **Redis Cloud** | Redis Labs | Free/Paid | Caching + Task queue |

### Optional Services
| Service | Purpose | When to Use |
|---------|---------|-------------|
| **Auth0 / Clerk** | User authentication | Production multi-user |
| **AWS S3 / MinIO** | PDF storage | Large-scale deployment |
| **PostHog / Mixpanel** | Analytics | User behavior tracking |

---

## 📦 Installation Commands

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
# or
yarn install
```

### Docker Setup
```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

---

## 🔧 Environment Variables Required

### Backend (.env)
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:5173"]

# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net
MONGO_DB=legal_db
MONGO_COLLECTION=legal_chunks

# AI Services
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile

EMBED_PROVIDER=mistral
EMBED_API_KEY=...
EMBED_MODEL_NAME=mistral-embed

RERANK_PROVIDER=cohere
RERANK_API_KEY=...
RERANK_MODEL_NAME=rerank-english-v3.0

VISION_PROVIDER=groq
VISION_API_KEY=gsk_...
VISION_MODEL_NAME=llama-3.2-11b-vision-preview

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Search Configuration
VECTOR_SEARCH_TOP_K=20
BM25_TOP_K=20
HYBRID_VECTOR_WEIGHT=0.6
HYBRID_BM25_WEIGHT=0.4
RERANK_TOP_K=5

# Monitoring
SENTRY_DSN=https://...
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
```

---

## 📊 System Requirements

### Development Environment
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Storage** | 20 GB | 50+ GB SSD |
| **OS** | macOS, Linux, Windows 10+ | Linux/macOS |
| **Python** | 3.10+ | 3.11+ |
| **Node.js** | 18+ | 20+ LTS |

### Production Environment
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 8 cores | 16+ cores |
| **RAM** | 16 GB | 32+ GB |
| **Storage** | 100 GB SSD | 500+ GB SSD |
| **Network** | 100 Mbps | 1 Gbps |

---

## 🚀 Deployment Options

### Option 1: Docker (Recommended)
- **Pros**: Consistent environments, easy scaling
- **Cons**: Requires Docker knowledge
- **Best For**: Production deployments

### Option 2: Cloud Platforms
| Platform | Service | Configuration |
|----------|---------|---------------|
| **AWS** | ECS + RDS + S3 | Container-based |
| **GCP** | Cloud Run + MongoDB Atlas | Serverless |
| **Azure** | App Service + Cosmos DB | PaaS |
| **Railway** | All-in-one | Easiest setup |

### Option 3: VPS
- **Providers**: DigitalOcean, Linode, Hetzner
- **Setup**: Manual deployment with systemd
- **Best For**: Cost-conscious deployments

---

## 📈 Scalability Considerations

### Horizontal Scaling
- **API**: Multiple FastAPI instances behind load balancer
- **Workers**: Scale Celery workers independently
- **Frontend**: CDN distribution (Cloudflare, Vercel)

### Vertical Scaling
- **MongoDB**: Upgrade to M20/M30 clusters
- **Redis**: Increase memory allocation
- **API**: Larger EC2/GCP instances

### Caching Strategy
- **Redis**: Cache embeddings (24h TTL)
- **Browser**: Cache static assets (7d)
- **CDN**: Cache frontend bundle

---

## 🔐 Security Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Transport** | TLS 1.3 | HTTPS encryption |
| **API** | slowapi | Rate limiting |
| **Auth** | JWT + bcrypt | Token-based auth |
| **Database** | MongoDB Atlas IP Whitelist | Network security |
| **Secrets** | python-dotenv | Environment variables |
| **Monitoring** | Sentry | Security alerts |

---

## 📚 Additional Resources

### Documentation
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [React Best Practices](https://react.dev/learn)

### API Documentation
- [Groq API Docs](https://console.groq.com/docs)
- [Mistral AI Docs](https://docs.mistral.ai/)
- [Cohere Rerank API](https://docs.cohere.com/reference/rerank)

---

## 🎯 Tech Stack Summary

**Total Technologies**: 60+

**Categories**:
- Backend: 25+ libraries/services
- Frontend: 20+ libraries/tools
- DevOps: 15+ tools
- External APIs: 4 AI services

**Primary Languages**:
- Python 3.10+ (Backend)
- JavaScript/TypeScript (Frontend)
- Docker (Infrastructure)

**Key Differentiators**:
- ✅ Hybrid search (Vector + BM25)
- ✅ Multi-strategy PDF parsing
- ✅ Production-grade RAG pipeline
- ✅ Dual knowledge base (Laws + Judgments)
- ✅ 6 specialized legal features

---

*This tech stack is designed for production-grade deployment with scalability, maintainability, and cost-efficiency in mind.*
