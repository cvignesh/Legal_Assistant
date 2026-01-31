export type JobStatus =
    | 'queued'
    | 'parsing'
    | 'preview_ready'
    | 'indexing'
    | 'completed'
    | 'failed';

export interface UploadJob {
    jobId: string;
    filename: string;
    type: 'act' | 'judgment';
    status: JobStatus;
    error?: string;
    summary?: {
        case_title?: string;
        total_chunks?: number;
        [key: string]: any;
    };
    createdAt: string;
}

export interface UploadResponse {
    job_id: string;
    filename: string;
    status: JobStatus;
}

export interface JobStatusResponse {
    job_id: string;
    status: JobStatus;
    filename: string;
    error?: string;
    summary?: any;
}

export interface Precedent {
    case_title: string;
    court: string;
    year: string | number | null;
    outcome: string;
    score: number;
    snippet: string;
}

export interface PredictionResult {
    viability_score: number;
    viability_label: string;
    total_analyzed: number;
    favorable_count: number;
    top_precedents: Precedent[];
    strategic_advice: string;
}

