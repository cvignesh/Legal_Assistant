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
