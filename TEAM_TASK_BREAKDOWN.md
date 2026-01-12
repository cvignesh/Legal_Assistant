# Legal Assistant - Team Task Categorization 

> **Project**: AI-Powered Legal Research & Petition Drafting Platform  
> **Team Size**: 9 Members  
> **Last Updated**: January 12, 2026

---

## 🎯 Team Organization

Our team is organized into **5 strategic units**. Each group consists of **2 members** to allow for peer review, pair programming, and knowledge sharing.

---

## 👥 Group Structure

### **Group A: PDF Engineering & Document Ingestion**
**Members**: Member 1 (Lead), Member 2 (Developer)  
**Focus**: Converting raw legal PDFs (BNS, BNSS, BSA) into structured, searchable chunks.

#### **Task 1: Smart PDF Parser Development**
Build the multi-strategy parser using `pdfplumber` and Groq Vision to detect sections, illustrations, provisos, and schedules.

**Responsibilities**:
- **Member 1**: Design parser architecture, mode detection algorithm, strategy pattern implementation
- **Member 2**: Implement 3 parsing strategies (Narrative, Strict, Schedule), text enrichment, OCR fallback

**Deliverables**:
- `app/parser/manager.py` - Main orchestrator
- `app/parser/strategies/narrative.py` - BNS/BSA parser
- `app/parser/strategies/strict.py` - BNSS/Tax Acts parser
- `app/parser/strategies/schedule.py` - PMLA/Schedule parser
- `app/parser/extractors/vision_extractor.py` - Groq Vision OCR
- `app/parser/enrichers/text_enricher.py` - Context prepending

**Content Covered**:
- Section detection regex patterns
- Illustration/Proviso attachment logic
- Schedule table parsing
- Vision LLM integration for scanned PDFs
- Text enrichment: `[Act] > [Chapter] > [Section]`

---

#### **Task 2: Embedding & Ingestion Pipeline**
Develop the embedding service and batch ingestion pipeline with progress tracking.

**Responsibilities**:
- **Member 1**: Design ingestion workflow, job queue management, error handling strategy
- **Member 2**: Implement Mistral embedding service, batch processing, CLI script, MongoDB upsert

**Deliverables**:
- `app/services/embedding_service.py` - Mistral API integration
- `app/services/ingestion_service.py` - Batch processing logic
- `scripts/ingest_batch.py` - CLI batch ingestion
- `app/api/ingestion_routes.py` - API endpoints

**Content Covered**:
- Mistral embedding API (1024-dim vectors)
- Batch processing with retry logic
- Progress tracking and status updates
- MongoDB bulk upsert operations
- Job queue management

**API Validation**: See [API_UI_VALIDATION_MATRIX.md](./API_UI_VALIDATION_MATRIX.md#feature-1-document-ingestion)

---

### **Group B: MongoDB Atlas & Retrieval Specialists**
**Members**: Member 3 (Search Engineer), Member 4 (Database Engineer)  
**Focus**: The "Search Brain" of the system - hybrid retrieval and database optimization.

#### **Task 1: Hybrid Search Engine Development**
Configure MongoDB Atlas Vector Search and BM25, then build the RRF (Reciprocal Rank Fusion) merger.

**Responsibilities**:
- **Member 3**: Implement vector search, BM25 search, RRF algorithm, Cohere reranking
- **Member 4**: Create MongoDB indexes, optimize queries, design schema, performance tuning

**Deliverables**:
- `app/services/vector_search.py` - Atlas Vector Search
- `app/services/bm25_search.py` - Atlas Text Search
- `app/services/rrf_merger.py` - RRF algorithm
- `app/services/retriever.py` - Hybrid orchestrator
- `app/services/reranker.py` - Cohere integration
- MongoDB Vector Index (1024-dim, cosine)
- MongoDB BM25 Text Index

**Content Covered**:
- MongoDB Atlas Vector Search (`$vectorSearch`)
- MongoDB Atlas Text Search (`$search`)
- RRF formula: `1 / (k + rank_i)`
- Weighted merging (0.6 Vector + 0.4 BM25)
- Cohere rerank-english-v3.0
- Score normalization (MinMax)

---

#### **Task 2: Database Schema & Performance Optimization**
Design the unified schema for laws and judgments, create indexes, and optimize query performance.

**Responsibilities**:
- **Member 4**: Schema design, index creation, migration scripts, performance monitoring
- **Member 3**: Query optimization, caching strategy (Redis), autocomplete service

**Deliverables**:
- `app/models/legal_chunk.py` - Pydantic models
- `app/models/judgment_chunk.py` - Judgment schema
- `app/services/database.py` - Motor async client
- `scripts/migrate_schema.py` - Migration automation
- `scripts/create_indexes.py` - Index automation
- `app/services/autocomplete_service.py` - Autocomplete

**Content Covered**:
- Normalized JSON schema (laws + judgments)
- Pydantic validation models
- Motor async MongoDB driver
- Index optimization strategies
- Redis caching for embeddings
- Autocomplete with prefix matching

**API Validation**: See [API_UI_VALIDATION_MATRIX.md](./API_UI_VALIDATION_MATRIX.md#feature-2-search)

---

### **Group C: AI Orchestration & RAG Pipeline**
**Members**: Member 5 (LLM Engineer), Member 6 (Backend Developer)  
**Focus**: Building the "Brain" using LangChain, Groq LLM, and conversational memory.

#### **Task 1: Core RAG Pipeline & Memory Management**
Develop the LangChain RAG chain with Groq LLM and MongoDB-backed conversation memory.

**Responsibilities**:
- **Member 5**: LLM integration, RAG chain design, prompt engineering, memory strategy
- **Member 6**: Memory implementation, session management, API endpoints, streaming support

**Deliverables**:
- `app/services/llm_engine.py` - Groq LLM integration
- `app/services/memory_manager.py` - MongoDB chat history
- `app/services/rag_chain.py` - LangChain RAG
- `app/services/prompts/chat_prompt.py` - System prompts
- `app/api/chat_routes.py` - Chat API

**Content Covered**:
- Groq API (Llama-3.3-70b-versatile)
- LangChain `ChatGroq` wrapper
- `ConversationSummaryBufferMemory`
- MongoDB-backed chat history
- History-aware retrieval
- Context injection and source tracking

---

#### **Task 2: Advanced Legal Features (Viability, Arguments, Clauses)**
Build specialized AI features for case prediction, argument mining, and clause search.

**Responsibilities**:
- **Member 5**: Design algorithms, prompt engineering, LLM orchestration for advanced features
- **Member 6**: Implement API endpoints, integrate with retrieval, build response formatters

**Deliverables**:
- `app/services/viability_service.py` - Case outcome prediction
- `app/services/argument_service.py` - Argument extraction
- `app/services/clause_service.py` - Clause search
- `app/services/prompts/viability_prompt.py` - Prompts
- `app/services/prompts/argument_prompt.py` - Prompts
- `app/services/prompts/clause_prompt.py` - Prompts
- `app/api/viability_routes.py` - API endpoints
- `app/api/argument_routes.py` - API endpoints
- `app/api/clause_routes.py` - API endpoints

**Content Covered**:
- Viability prediction algorithm (majority voting)
- Argument classification (prosecution/defense)
- Winning strategy identification
- Exact clause retrieval
- Judgment-based reasoning

**API Validation**: See [API_UI_VALIDATION_MATRIX.md](./API_UI_VALIDATION_MATRIX.md#feature-3-legal-chat)

---

### **Group D: Quality Assurance & Testing**
**Members**: Member 7 (QA Lead), Member 8 (Test Engineer)  
**Focus**: Ensuring the system produces reliable, accurate legal information through comprehensive testing.

#### **Task 1: API & Integration Testing**
Build comprehensive test suites for all backend services and API endpoints.

**Responsibilities**:
- **Member 7**: Test strategy, test plan, API validation, Postman collections
- **Member 8**: Unit tests, integration tests, pytest automation, test fixtures

**Deliverables**:
- `tests/test_parser.py` - Parser unit tests
- `tests/test_search.py` - Search service tests
- `tests/test_retriever.py` - Retrieval tests
- `tests/test_api.py` - API integration tests
- `tests/conftest.py` - Pytest configuration
- `tests/fixtures/` - Test data
- `postman/Legal_Assistant.postman_collection.json`

**Content Covered**:
- pytest framework
- FastAPI TestClient
- Mocking MongoDB queries
- Testing async functions
- API endpoint validation
- Error scenario testing
- Test coverage reporting (>80%)

---

#### **Task 2: AI Quality Evaluation & DeepEval Integration**
Integrate DeepEval framework to validate AI-generated responses for quality, accuracy, and reliability.

**Responsibilities**:
- **Member 7**: DeepEval integration, metric configuration, quality threshold definition, evaluation reporting
- **Member 8**: Automated evaluation pipeline, regeneration logic, quality score logging, performance testing

**Deliverables**:
- `app/services/evaluation_service.py` - DeepEval integration
- `app/services/metrics/` - Custom evaluation metrics
  - `faithfulness_metric.py` - Verify answers are grounded in sources
  - `relevancy_metric.py` - Check answer relevance to query
  - `answer_relevancy_metric.py` - Measure answer quality
  - `contextual_precision_metric.py` - Validate context accuracy
- `app/services/regeneration_service.py` - Auto-regeneration on low scores
- `tests/test_evaluation.py` - Evaluation tests
- `scripts/evaluate_responses.py` - Batch evaluation script
- `docs/EVALUATION_METRICS.md` - Metrics documentation

**Content Covered**:
- DeepEval framework integration
- Faithfulness metric (answers grounded in retrieved context)
- Answer Relevancy metric (answers address the query)
- Contextual Precision metric (retrieved context is accurate)
- Contextual Recall metric (all relevant context retrieved)
- Quality threshold configuration
- Automated regeneration logic
- Evaluation score logging to MongoDB
- Performance impact monitoring

**Evaluation Metrics**:
- **Faithfulness Score**: ≥ 0.8 (answers must be factually grounded)
- **Answer Relevancy Score**: ≥ 0.7 (answers must address query)
- **Contextual Precision Score**: ≥ 0.75 (context must be accurate)
- **Contextual Recall Score**: ≥ 0.7 (all relevant context retrieved)
- **Overall Quality Score**: ≥ 0.75 (weighted average)

**Regeneration Logic**:
- If any metric < threshold → Trigger regeneration (max 3 attempts)
- Log all scores to MongoDB for analysis
- Alert on repeated failures

---

#### **Task 3: UI Testing & End-to-End Validation**
Validate all UI components and complete user flows from API to UI.

**Responsibilities**:
- **Member 7**: E2E test design, manual UI testing, screenshot documentation, bug tracking
- **Member 8**: Playwright automation, component tests, performance testing

**Deliverables**:
- `e2e/ingestion.spec.js` - Ingestion flow tests
- `e2e/search.spec.js` - Search flow tests
- `e2e/chat.spec.js` - Chat flow tests
- `e2e/viability.spec.js` - Viability predictor tests
- `e2e/arguments.spec.js` - Argument miner tests
- `e2e/clauses.spec.js` - Clause search tests
- `playwright.config.js` - Playwright setup
- `docs/TEST_PLAN.md` - Test strategy
- `docs/TEST_CASES.md` - Test cases
- UI screenshots for all features

**Content Covered**:
- Playwright E2E testing
- Browser automation
- Visual regression testing
- Screenshot comparison
- Manual UI validation
- Bug reporting workflow
- Performance benchmarking

**UI Validation**: See [API_UI_VALIDATION_MATRIX.md](./API_UI_VALIDATION_MATRIX.md)

---

### **Group E: Frontend & User Experience**
**Members**: Member 9 (Frontend Lead), Member 10 (UI Developer)  
**Focus**: The user experience and the final deliverable - a beautiful, intuitive React interface.

#### **Task 1: React Application Architecture & Core Components**
Build the React application framework with Material UI and core reusable components.

**Responsibilities**:
- **Member 9**: Architecture design, routing, state management, theme, API client
- **Member 10**: Component library, common UI elements, layout components

**Deliverables**:
- `frontend/src/App.jsx` - Main application
- `frontend/src/theme/theme.js` - MUI theme (Enterprise Blue)
- `frontend/src/routes.jsx` - Routing configuration
- `frontend/src/stores/` - Zustand state stores
- `frontend/src/services/api.js` - Axios client
- `frontend/src/components/common/` - Reusable components
- `frontend/src/components/layout/` - Layout components

**Content Covered**:
- React 18 + Vite setup
- Material UI (MUI) theming
- React Router v6
- Zustand state management
- TanStack Query (React Query)
- Axios HTTP client
- Component composition patterns

---

#### **Task 2: Feature UI Development (6 Tabs)**
Develop the UI for all 6 features: Ingestion, Search, Chat, Viability, Arguments, Clauses.

**Responsibilities**:
- **Member 9**: Ingestion UI, Search UI, Chat UI (complex interactions)
- **Member 10**: Viability UI, Arguments UI, Clauses UI (form-heavy features)

**Deliverables**:
- `frontend/src/components/ingestion/` - Upload, progress tracking
- `frontend/src/components/search/` - Search bar, filters, results
- `frontend/src/components/chat/` - Chat interface, source chips
- `frontend/src/components/viability/` - Prediction form, results
- `frontend/src/components/arguments/` - Argument display
- `frontend/src/components/clauses/` - Clause search, copy

**Content Covered**:
- react-dropzone for file upload
- MUI TextField, Autocomplete, Card
- Real-time progress polling
- Pagination components
- Chat message rendering
- Source citation chips
- Form handling (React Hook Form + Zod)
- Copy-to-clipboard functionality
- Responsive design (mobile + desktop)

**UI Validation**: See [API_UI_VALIDATION_MATRIX.md](./API_UI_VALIDATION_MATRIX.md)

---
