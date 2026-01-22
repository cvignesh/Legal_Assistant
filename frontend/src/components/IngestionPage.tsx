import { useState, useEffect, useCallback, useRef } from 'react';
import { UploadJob, JobStatus } from '../types';
import { actsAPI, judgmentsAPI } from '../api';
import './IngestionPage.css';

const IngestionPage = () => {
    const [activeTab, setActiveTab] = useState<'acts' | 'judgments'>('judgments');
    const [jobs, setJobs] = useState<UploadJob[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Poll job statuses every 3 seconds
    useEffect(() => {
        const activeJobs = jobs.filter(j =>
            ['queued', 'parsing', 'indexing'].includes(j.status)
        );

        if (activeJobs.length === 0) return;

        const pollInterval = setInterval(() => {
            activeJobs.forEach(async (job) => {
                try {
                    const api = job.type === 'act' ? actsAPI : judgmentsAPI;
                    const status = await api.getStatus(job.jobId);

                    setJobs(prev => prev.map(j =>
                        j.jobId === job.jobId
                            ? { ...j, status: status.status, error: status.error, summary: status.summary }
                            : j
                    ));
                } catch (error) {
                    console.error('Failed to fetch status:', error);
                }
            });
        }, 3000);

        return () => clearInterval(pollInterval);
    }, [jobs]);

    const handleFileSelect = async (files: FileList) => {
        const fileArray = Array.from(files);

        try {
            if (activeTab === 'judgments') {
                // Batch upload for judgments
                const response = await judgmentsAPI.upload(fileArray);
                const newJobs: UploadJob[] = response.jobs.map(job => ({
                    jobId: job.job_id,
                    filename: job.filename,
                    type: 'judgment',
                    status: job.status,
                    createdAt: new Date().toISOString(),
                }));
                setJobs(prev => [...newJobs, ...prev]);
            } else {
                // Single file for acts
                const file = fileArray[0];
                const response = await actsAPI.upload(file);
                const newJob: UploadJob = {
                    jobId: response.job_id,
                    filename: response.filename,
                    type: 'act',
                    status: response.status,
                    createdAt: new Date().toISOString(),
                };
                setJobs(prev => [newJob, ...prev]);
            }
        } catch (error: any) {
            console.error('Upload failed:', error);
            alert(`Upload failed: ${error.message}`);
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files) {
            handleFileSelect(e.dataTransfer.files);
        }
    }, [activeTab]);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleConfirm = async (jobId: string, type: 'act' | 'judgment') => {
        try {
            const api = type === 'act' ? actsAPI : judgmentsAPI;
            await api.confirm(jobId);

            setJobs(prev => prev.map(j =>
                j.jobId === jobId ? { ...j, status: 'indexing' as JobStatus } : j
            ));
        } catch (error: any) {
            alert(`Confirmation failed: ${error.message}`);
        }
    };

    const getStageInfo = (status: JobStatus) => {
        const stages = {
            queued: { label: 'Queued', stage: 0, color: 'grey' },
            parsing: { label: 'Parsing', stage: 1, color: 'blue' },
            preview_ready: { label: 'Preview Ready', stage: 2, color: 'yellow' },
            indexing: { label: 'Indexing', stage: 3, color: 'blue' },
            completed: { label: 'Completed', stage: 4, color: 'green' },
            failed: { label: 'Failed', stage: -1, color: 'red' },
        };
        return stages[status];
    };

    return (
        <div className="ingestion-page">
            <header className="header">
                <h1>📁 Legal Document Ingestion</h1>
            </header>

            <div className="tabs">
                <button
                    className={activeTab === 'acts' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('acts')}
                >
                    Upload Acts/Laws
                </button>
                <button
                    className={activeTab === 'judgments' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('judgments')}
                >
                    Upload Judgments
                </button>
            </div>

            <div
                className={`upload-zone ${isDragging ? 'dragging' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
            >
                <div className="upload-icon">☁️</div>
                <p>Drag & Drop your legal files here, or browse to upload.</p>
                <p className="upload-hint">Supported file types: PDF, DOCX. Max file size: 200MB.</p>
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple={activeTab === 'judgments'}
                    accept=".pdf,.docx"
                    style={{ display: 'none' }}
                    onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
                />
            </div>

            <div className="jobs-section">
                <h2>Batch Upload Queue ({jobs.length} files)</h2>

                {jobs.length === 0 ? (
                    <div className="empty-state">
                        <p>📂 No files uploaded yet</p>
                        <p>Drag & drop to get started</p>
                    </div>
                ) : (
                    <div className="jobs-list">
                        {jobs.map(job => {
                            const stageInfo = getStageInfo(job.status);
                            return (
                                <div key={job.jobId} className="job-card">
                                    <div className="job-header">
                                        <span className="job-icon">📄</span>
                                        <div className="job-info">
                                            <h3>{job.filename}</h3>
                                            <span className="job-type">{job.type.toUpperCase()}</span>
                                        </div>
                                        <span className={`status-badge ${stageInfo.color}`}>
                                            {stageInfo.label}
                                        </span>
                                    </div>

                                    <div className="stage-indicator">
                                        {['Upload', 'Parse', 'Chunk', 'Embed', 'Index'].map((label, idx) => (
                                            <div key={idx} className="stage">
                                                <div className={`stage-dot ${job.status === 'completed' ? 'completed' : idx < stageInfo.stage ? 'completed' : idx === stageInfo.stage ? 'active' : 'pending'}`} />
                                                <span>{label}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {job.error && (
                                        <div className="error-message">❌ {job.error}</div>
                                    )}

                                    {job.status === 'preview_ready' && (
                                        <button
                                            className="confirm-btn"
                                            onClick={() => handleConfirm(job.jobId, job.type)}
                                        >
                                            ✓ Review & Confirm
                                        </button>
                                    )}

                                    {job.status === 'completed' && job.summary && (
                                        <div className="summary">
                                            ✅ {job.summary.total_chunks} chunks indexed successfully
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default IngestionPage;
