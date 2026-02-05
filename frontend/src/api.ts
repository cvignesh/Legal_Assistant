import axios from 'axios';
import { UploadResponse, JobStatusResponse } from './types';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Acts/Laws API
export const actsAPI = {
    upload: async (files: File[]): Promise<{ jobs: UploadResponse[] }> => {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        const { data } = await api.post('/ingest/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    },

    getStatus: async (jobId: string): Promise<JobStatusResponse> => {
        const { data } = await api.get(`/ingest/${jobId}/status`);
        return data;
    },

    confirm: async (jobId: string) => {
        const { data } = await api.post(`/ingest/${jobId}/confirm`);
        return data;
    }
};

// Judgments API
export const judgmentsAPI = {
    upload: async (files: File[]): Promise<{ jobs: UploadResponse[] }> => {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        const { data } = await api.post('/judgments/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    },

    getStatus: async (jobId: string): Promise<JobStatusResponse> => {
        const { data } = await api.get(`/judgments/${jobId}/status`);
        return data;
    },

    confirm: async (jobId: string) => {
        const { data } = await api.post(`/judgments/${jobId}/confirm`);
        return data;
    }
};

// Viability API
export const viabilityAPI = {
    predict: async (facts: string, role: string, courtFilter: string) => {
        const { data } = await api.post('/viability', {
            facts,
            user_role: role,
            court_filter: courtFilter
        });
        return data;
    }
};

// Drafting API
export const draftingAPI = {
    generateDraft: async (userStory: string, documentType: string) => {
        const { data } = await api.post('/drafting/generate', {
            user_story: userStory,
            document_type: documentType
        });
        return data;
    }
};
