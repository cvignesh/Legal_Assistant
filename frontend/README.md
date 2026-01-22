# Legal Assistant - Frontend

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Backend (Required)
In a separate terminal:
```bash
cd backend
uvicorn app.main:app
```
Backend must be running on `http://localhost:8000`

### 3. Start Frontend
```bash
npm run dev
```

Frontend will start at `http://localhost:3000`

## Features

- **Drag & Drop Upload**: Upload Acts/Laws or Judgments
- **Batch Processing**: Upload multiple files simultaneously
- **Real-time Status**: Auto-refreshing progress (polls every 3s)
- **Stage Tracking**: Visual indicators for each processing stage
- **Tab Switching**: Separate upload zones for Acts and Judgments

## Tech Stack

- React 18 + TypeScript
- Vite (dev server)
- Axios (API calls)
- CSS3 (no frameworks)

## API Integration

The frontend connects to these backend endpoints:

**Acts/Laws:**
- `POST /api/ingest/upload`
- `GET /api/ingest/{job_id}/status`
- `POST /api/ingest/{job_id}/confirm`

**Judgments:**
- `POST /api/judgments/upload`
- `GET /api/judgments/{job_id}/status`
- `POST /api/judgments/{job_id}/confirm`

Proxy is configured in `vite.config.ts` to forward `/api/*` to `http://localhost:8000`.
