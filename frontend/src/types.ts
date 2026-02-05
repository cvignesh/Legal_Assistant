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

// Petition Drafting Types
export type DocumentType = 'police_complaint' | 'magistrate_156_3' | 'private_complaint_200' | 'legal_notice';

export interface DraftingRequest {
    user_story: string;
    document_type: DocumentType;
}

export interface FactExtractionResult {
    chronology: string[];
    accused_details: string;
    complainant_details: string;
    core_allegation: string;
    monetary_details: string;
    place_of_occurence: string;
    date_of_occurence: string;
}

export interface LegalIssue {
    act: string;
    section: string;
    reasoning: string;
    section_title?: string;
    section_full_text?: string;
    punishment?: string;
    is_validated?: boolean;
}

export interface ValidatedCitation {
    case_title: string;
    citation_source: string;
    excerpt: string;
    relevance_score: number;
    relevance_explanation: string;
    pdf_url?: string;
}

export interface DraftingResponse {
    draft_text: string;
    facts: FactExtractionResult;
    legal_issues: LegalIssue[];
    citations: ValidatedCitation[];
    validation_warnings: string[];
    procedural_analysis?: ProceduralAnalysis;
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ProceduralAnalysis {
    risk_level: RiskLevel;
    issues: string[];
    missing_mandatory_components: string[];
    suggestions: string[];
    score: number;
}
