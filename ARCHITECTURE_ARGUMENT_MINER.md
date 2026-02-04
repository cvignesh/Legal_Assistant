# Argument Miner Architecture & Workflow

## Overview
The Argument Miner is a system designed to extract, normalize, and validate legal arguments from court judgments using retrieval-augmented generation (RAG) and LLM-based processing. It supports multiple modes (e.g., Facts, Case ID) and is built with a modular, service-oriented backend and a React frontend.

---

## High-Level Architecture

```
+-------------------+      +-------------------+      +-------------------+
|   Frontend (UI)   | <--> |   FastAPI Backend | <--> |   MongoDB/Vector  |
|  (React/TS)       |      |  (Python)         |      |   DB (Chunks)     |
+-------------------+      +-------------------+      +-------------------+
```

- **Frontend**: User selects mode, enters query/case ID, views arguments.
- **Backend**: Handles API requests, argument mining pipeline, LLM calls.
- **Database**: Stores judgment chunks, metadata, and vector embeddings.

---

## Detailed Workflow

### 1. User Request
- User selects mode (e.g., Facts, Case ID) and submits a query or case ID via the frontend.
- Frontend sends a request to `/api/argument-miner` with the relevant parameters.

### 2. Backend Pipeline
#### a. Routing
- FastAPI endpoint receives the request and routes it to the appropriate miner (e.g., `fact_miner`, `case_miner`).

#### b. Chunk Retrieval
- The miner calls `retrieve_arguments` with filters (e.g., `case_number`, `section_type`).
- `retrieve_arguments` uses `vector_search` to query the vector DB for relevant chunks.
- Chunks are filtered by role (prosecution/defense) and case metadata.

#### c. Normalization
- Retrieved chunks are passed to `normalize_arguments`.
- All chunk contents are batched and sent to the LLM with a prompt to extract only legal arguments.
- The LLM returns a list of arguments, which are parsed and deduplicated.

#### d. Validation (Optional)
- Arguments can be validated using a separate LLM validator, which checks correctness and relevance.

#### e. Response
- The backend returns the final list of prosecution and defense arguments to the frontend.

### 3. Frontend Display
- Arguments are displayed in the UI, grouped by role.

---

## Key Components

### Backend
- **FastAPI App**: Main entry point for API requests.
- **argument_miner.service**: Orchestrates the mining pipeline.
- **argument_miner.case_miner / fact_miner**: Mode-specific logic.
- **argument_miner.retriever**: Handles chunk retrieval from the vector DB.
- **argument_miner.normalizer**: Batches and normalizes arguments using LLM.
- **argument_miner.llm_validator**: (Optional) Validates arguments with LLM.
- **MongoDB/Vector DB**: Stores judgment chunks and embeddings.

### Frontend
- **React Components**: UI for input, mode selection, and argument display.
- **API Layer**: Handles communication with the backend.

---

## Data Flow Diagram

```
User (UI)
   |
   v
[API Request]
   |
   v
[FastAPI Endpoint]
   |
   v
[Argument Miner Pipeline]
   |    |    |
   |    |    +--> [Retriever: vector_search + filters]
   |    |          |
   |    |          v
   |    |      [Chunks]
   |    |
   |    +--> [Normalizer: LLM batch extraction]
   |               |
   |               v
   |           [Arguments]
   |
   +--> [Validator: LLM (optional)]
   |
   v
[API Response]
   |
   v
User (UI)
```

---

## Implementation Notes
- **Chunking**: Judgments are pre-processed into chunks with metadata (case number, section type, etc.) and embedded for vector search.
- **Retrieval**: Uses semantic search with filters for role and case.
- **LLM Normalization**: All chunk texts are batched for efficient LLM calls; output is parsed and deduplicated.
- **Extensibility**: New modes or validators can be added by extending the miner pipeline.
- **Logging**: Detailed logs at each stage for debugging and traceability.

---

## Example API Flow (Case ID Mode)
1. User enters a case ID and selects "Case ID" mode.
2. Frontend sends `{ "mode": "case_id", "case_id": "H.C.P(MD)No.633 of 2019" }` to backend.
3. Backend retrieves prosecution and defense chunks for the case.
4. Chunks are normalized in batch by the LLM.
5. Deduplicated arguments are returned and displayed in the UI.

---

## References
- `backend/app/services/argument_miner/`
- `frontend/src/components/ArgumentMiner.tsx`
- MongoDB/Vector DB schema for chunk storage

---

For further details, see the code in the referenced backend and frontend files.
