import React, { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Typography,
    Paper,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Card,
    CardContent,
    Grid,
    CircularProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Chip,
    Alert,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Description,
    ExpandMore,
    ContentCopy,
    Gavel,
    CheckCircle,
    Warning,
    Security,
    ErrorOutline
} from '@mui/icons-material';
import { draftingAPI } from '../api';
import { DraftingResponse, DocumentType } from '../types';

const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
    { value: 'police_complaint', label: 'Police Complaint' },
    { value: 'magistrate_156_3', label: 'Magistrate Petition u/s 156(3)' },
    { value: 'private_complaint_200', label: 'Private Complaint u/s 200' },
    { value: 'legal_notice', label: 'Legal Notice' }
];

const LOADING_STAGES = [
    { icon: '🔍', text: 'Extracting facts from your story...', duration: 4000 },
    { icon: '⚖️', text: 'Identifying applicable legal sections...', duration: 4000 },
    { icon: '✓', text: 'Verifying statutes in database...', duration: 4000 },
    { icon: '📚', text: 'Searching relevant judgments...', duration: 8000 },
    { icon: '🎯', text: 'Analyzing citation relevance...', duration: 8000 },
    { icon: '📝', text: 'Drafting your petition...', duration: 0 }
];

const PetitionDrafter: React.FC = () => {
    const [userStory, setUserStory] = useState('');
    const [documentType, setDocumentType] = useState<DocumentType>('police_complaint');
    const [loading, setLoading] = useState(false);
    const [loadingStage, setLoadingStage] = useState(0);
    const [result, setResult] = useState<DraftingResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const handleGenerate = async () => {
        if (!userStory.trim()) return;

        setLoading(true);
        setLoadingStage(0);
        setError(null);
        setResult(null);
        setCopied(false);

        // Simulate progress stages - cycle through all stages continuously
        let currentStage = 0;
        const stageInterval = setInterval(() => {
            currentStage = (currentStage + 1) % LOADING_STAGES.length; // Loop back to 0 after last stage
            setLoadingStage(currentStage);
        }, 4000); // Change stage every 4 seconds

        try {
            const data = await draftingAPI.generateDraft(userStory, documentType);
            clearInterval(stageInterval);
            setResult(data);
        } catch (err: any) {
            clearInterval(stageInterval);
            setError(err.response?.data?.detail || "Failed to generate draft");
        } finally {
            setLoading(false);
            setLoadingStage(0);
        }
    };

    const handleCopyDraft = () => {
        if (result?.draft_text) {
            navigator.clipboard.writeText(result.draft_text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Description /> Petition Drafting Engine
            </Typography>
            <Typography variant="subtitle1" color="text.secondary" paragraph>
                Generate court-ready legal documents with AI-powered fact extraction and grounded legal reasoning.
            </Typography>

            {/* Input Section */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
                <Grid container spacing={3}>
                    <Grid size={12}>
                        <TextField
                            label="Your Legal Story"
                            multiline
                            rows={6}
                            fullWidth
                            value={userStory}
                            onChange={(e) => setUserStory(e.target.value)}
                            placeholder="Describe your situation in detail (e.g., 'I gave Rs. 10 Lakhs to Mr. X on 1st Jan 2024 for a business investment. He promised to return it by 1st March 2024...')"
                            variant="outlined"
                        />
                    </Grid>
                    <Grid size={12}>
                        <FormControl fullWidth>
                            <InputLabel>Document Type</InputLabel>
                            <Select
                                value={documentType}
                                label="Document Type"
                                onChange={(e) => setDocumentType(e.target.value as DocumentType)}
                            >
                                {DOCUMENT_TYPES.map(type => (
                                    <MenuItem key={type.value} value={type.value}>
                                        {type.label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid size={12}>
                        <Button
                            variant="contained"
                            size="large"
                            onClick={handleGenerate}
                            disabled={loading || !userStory}
                            startIcon={loading ? <CircularProgress size={20} /> : <Gavel />}
                            fullWidth
                        >
                            {loading ? "Generating Draft..." : "Generate Draft"}
                        </Button>


                        {/* Multi-Stage Loading - Round Robin */}
                        {loading && (
                            <Paper elevation={2} sx={{ mt: 3, p: 3, bgcolor: '#f5f5f5', textAlign: 'center' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
                                    <Typography variant="h3">{LOADING_STAGES[loadingStage].icon}</Typography>
                                    <Typography variant="body1" fontWeight="medium">
                                        {LOADING_STAGES[loadingStage].text}
                                    </Typography>
                                </Box>
                            </Paper>
                        )}

                        {error && (
                            <Alert severity="error" sx={{ mt: 2 }}>
                                {error}
                            </Alert>
                        )}
                    </Grid>
                </Grid>
            </Paper>

            {/* Results Section */}
            {result && (
                <Box>
                    {/* Procedural Analysis Report - The Gatekeeper */}
                    {result.procedural_analysis && (
                        <Paper
                            variant="outlined"
                            sx={{
                                mb: 3,
                                p: 2,
                                borderColor: result.procedural_analysis.risk_level === 'CRITICAL' || result.procedural_analysis.risk_level === 'HIGH' ? '#d32f2f' : result.procedural_analysis.risk_level === 'MEDIUM' ? '#ed6c02' : '#2e7d32',
                                borderLeftWidth: 6,
                                bgcolor: '#fafafa'
                            }}
                        >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                <Box>
                                    <Typography variant="h6" display="flex" alignItems="center" gap={1}>
                                        <Security color={result.procedural_analysis.risk_level === 'CRITICAL' || result.procedural_analysis.risk_level === 'HIGH' ? 'error' : 'action'} />
                                        Procedural Health Check
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Automated audit of procedural pre-conditions and statutory bars.
                                    </Typography>
                                </Box>
                                <Chip
                                    label={`Risk: ${result.procedural_analysis.risk_level} (${result.procedural_analysis.score}/100)`}
                                    color={result.procedural_analysis.risk_level === 'CRITICAL' || result.procedural_analysis.risk_level === 'HIGH' ? 'error' : result.procedural_analysis.risk_level === 'MEDIUM' ? 'warning' : 'success'}
                                    sx={{ fontWeight: 'bold' }}
                                />
                            </Box>

                            <Grid container spacing={2}>
                                {result.procedural_analysis.issues.length > 0 && (
                                    <Grid size={12}>
                                        <Alert severity="error" icon={<ErrorOutline />} sx={{ '& .MuiAlert-message': { width: '100%' } }}>
                                            <Typography variant="subtitle2">Critical Procedural Issues:</Typography>
                                            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                                                {result.procedural_analysis.issues.map((issue, i) => (
                                                    <li key={i}><Typography variant="body2">{issue}</Typography></li>
                                                ))}
                                            </ul>
                                        </Alert>
                                    </Grid>
                                )}

                                {result.procedural_analysis.missing_mandatory_components.length > 0 && (
                                    <Grid size={12}>
                                        <Alert severity="warning" icon={<Warning />} sx={{ '& .MuiAlert-message': { width: '100%' } }}>
                                            <Typography variant="subtitle2">Missing Mandatory Components:</Typography>
                                            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                                                {result.procedural_analysis.missing_mandatory_components.map((item, i) => (
                                                    <li key={i}><Typography variant="body2">{item}</Typography></li>
                                                ))}
                                            </ul>
                                        </Alert>
                                    </Grid>
                                )}

                                {result.procedural_analysis.suggestions.length > 0 && (
                                    <Grid size={12}>
                                        <Alert severity="info" sx={{ '& .MuiAlert-message': { width: '100%' } }}>
                                            <Typography variant="subtitle2">Suggestions:</Typography>
                                            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                                                {result.procedural_analysis.suggestions.map((suggestion, i) => (
                                                    <li key={i}><Typography variant="body2">{suggestion}</Typography></li>
                                                ))}
                                            </ul>
                                        </Alert>
                                    </Grid>
                                )}
                            </Grid>
                        </Paper>
                    )}

                    {/* Warnings */}
                    {result.validation_warnings.length > 0 && (
                        <Alert severity="warning" icon={<Warning />} sx={{ mb: 3 }}>
                            <Typography variant="subtitle2" gutterBottom>Validation Warnings:</Typography>
                            {result.validation_warnings.map((warning, idx) => (
                                <Typography key={idx} variant="body2">• {warning}</Typography>
                            ))}
                        </Alert>
                    )}

                    {/* Draft Text */}
                    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">Generated Draft</Typography>
                            <Tooltip title={copied ? "Copied!" : "Copy to clipboard"}>
                                <IconButton onClick={handleCopyDraft} color={copied ? "success" : "primary"}>
                                    {copied ? <CheckCircle /> : <ContentCopy />}
                                </IconButton>
                            </Tooltip>
                        </Box>
                        <TextField
                            multiline
                            fullWidth
                            value={result.draft_text}
                            variant="outlined"
                            InputProps={{
                                readOnly: true,
                                sx: { fontFamily: 'monospace', fontSize: '0.9rem' }
                            }}
                            minRows={15}
                            maxRows={25}
                        />
                    </Paper>

                    {/* Extracted Facts */}
                    <Accordion defaultExpanded>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                            <Typography variant="h6">Extracted Facts</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Grid container spacing={2}>
                                <Grid size={12}>
                                    <Typography variant="subtitle2" color="primary">Chronology:</Typography>
                                    {result.facts.chronology.map((event, idx) => (
                                        <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                                            {idx + 1}. {event}
                                        </Typography>
                                    ))}
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Complainant:</Typography>
                                    <Typography variant="body2">{result.facts.complainant_details}</Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Accused:</Typography>
                                    <Typography variant="body2">{result.facts.accused_details}</Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Core Allegation:</Typography>
                                    <Typography variant="body2">{result.facts.core_allegation}</Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Amount:</Typography>
                                    <Typography variant="body2">{result.facts.monetary_details}</Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Date:</Typography>
                                    <Typography variant="body2">{result.facts.date_of_occurence}</Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                    <Typography variant="subtitle2" color="primary">Place:</Typography>
                                    <Typography variant="body2">{result.facts.place_of_occurence}</Typography>
                                </Grid>
                            </Grid>
                        </AccordionDetails>
                    </Accordion>

                    {/* Legal Issues */}
                    <Accordion defaultExpanded sx={{ mt: 2 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                            <Typography variant="h6">Legal Issues ({result.legal_issues.length})</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {result.legal_issues.length === 0 ? (
                                <Typography variant="body2" color="text.secondary">
                                    No legal issues identified.
                                </Typography>
                            ) : (
                                <Grid container spacing={2}>
                                    {result.legal_issues.map((issue, idx) => (
                                        <Grid size={12} key={idx}>
                                            <Card variant="outlined">
                                                <CardContent>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                                            <Chip label={issue.act} color="primary" size="small" />
                                                            <Chip label={`Section ${issue.section}`} variant="outlined" size="small" />
                                                        </Box>

                                                        {/* Validation Badge */}
                                                        {issue.is_validated ? (
                                                            <Tooltip title="Verified in Internal Database">
                                                                <Chip
                                                                    icon={<CheckCircle style={{ color: 'white' }} />}
                                                                    label="Validated"
                                                                    size="small"
                                                                    sx={{ bgcolor: '#2e7d32', color: 'white', fontWeight: 'bold' }}
                                                                />
                                                            </Tooltip>
                                                        ) : (
                                                            <Tooltip title="Could not be verified in internal database - Manual verification required">
                                                                <Chip
                                                                    icon={<Warning style={{ color: '#663c00' }} />}
                                                                    label="Unverified Risk"
                                                                    size="small"
                                                                    sx={{ bgcolor: '#ffb74d', color: '#663c00', fontWeight: 'bold' }}
                                                                />
                                                            </Tooltip>
                                                        )}
                                                    </Box>

                                                    {/* Section Title */}
                                                    {issue.section_title && (
                                                        <Typography variant="subtitle2" fontWeight="bold" sx={{ mt: 1, mb: 0.5 }}>
                                                            {issue.section_title}
                                                        </Typography>
                                                    )}

                                                    {/* Reasoning */}
                                                    <Typography variant="body2" sx={{ mb: 2 }}>
                                                        {issue.reasoning}
                                                    </Typography>

                                                    {/* Expandable Section Details or Warning */}
                                                    {issue.is_validated ? (
                                                        issue.section_full_text && (
                                                            <Accordion sx={{ mt: 1, bgcolor: '#f9f9f9' }}>
                                                                <AccordionSummary expandIcon={<ExpandMore />}>
                                                                    <Typography variant="body2" color="primary" fontWeight="medium">
                                                                        📖 Show Full Section Details
                                                                    </Typography>
                                                                </AccordionSummary>
                                                                <AccordionDetails>
                                                                    <Box>
                                                                        {/* Full Section Text */}
                                                                        <Typography
                                                                            variant="body2"
                                                                            sx={{
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontFamily: 'Georgia, serif',
                                                                                lineHeight: 1.7,
                                                                                mb: 2
                                                                            }}
                                                                        >
                                                                            {issue.section_full_text}
                                                                        </Typography>

                                                                        {/* Punishment Details */}
                                                                        {issue.punishment && (
                                                                            <Alert severity="warning" sx={{ mt: 2 }}>
                                                                                <Typography variant="subtitle2" fontWeight="bold">
                                                                                    ⚖️ Punishment:
                                                                                </Typography>
                                                                                <Typography variant="body2">
                                                                                    {issue.punishment}
                                                                                </Typography>
                                                                            </Alert>
                                                                        )}
                                                                    </Box>
                                                                </AccordionDetails>
                                                            </Accordion>
                                                        )
                                                    ) : (
                                                        <Alert severity="warning" icon={<Warning />} sx={{ mt: 2 }}>
                                                            <Typography variant="subtitle2" fontWeight="bold">
                                                                Verification Failed
                                                            </Typography>
                                                            <Typography variant="body2">
                                                                We could not verify this section in our internal database. Please proceed with caution and verify manually.
                                                            </Typography>
                                                        </Alert>
                                                    )}
                                                </CardContent>
                                            </Card>
                                        </Grid>
                                    ))}
                                </Grid>
                            )}
                        </AccordionDetails>
                    </Accordion>

                    {/* Citations */}
                    <Accordion sx={{ mt: 2 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                            <Typography variant="h6">Grounded Citations ({result.citations.length})</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {result.citations.length === 0 ? (
                                <Typography variant="body2" color="text.secondary">
                                    No citations found (may not be required for this document type or no relevant judgments in database).
                                </Typography>
                            ) : (
                                <Grid container spacing={2}>
                                    {result.citations.map((citation, idx) => (
                                        <Grid size={12} key={idx}>
                                            <Card variant="outlined">
                                                <CardContent>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                        <Typography variant="subtitle1" fontWeight="bold">
                                                            {citation.case_title}
                                                        </Typography>
                                                        <Tooltip title="Verified in Internal Database">
                                                            <Chip
                                                                icon={<CheckCircle style={{ color: 'white' }} />}
                                                                label="Validated"
                                                                size="small"
                                                                sx={{ bgcolor: '#2e7d32', color: 'white', fontWeight: 'bold' }}
                                                            />
                                                        </Tooltip>
                                                    </Box>
                                                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                                                        Relevance: {(citation.relevance_score * 100).toFixed(0)}%
                                                    </Typography>

                                                    {/* Relevance Explanation */}
                                                    <Typography variant="body2" sx={{ mt: 2, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 1, borderLeft: '4px solid #1976d2' }}>
                                                        <strong>Why this is relevant:</strong> {citation.relevance_explanation}
                                                    </Typography>

                                                    {/* Excerpt */}
                                                    <Typography variant="body2" sx={{ mt: 1.5, fontStyle: 'italic', bgcolor: '#f9f9f9', p: 1, borderRadius: 1 }}>
                                                        "{citation.excerpt}"
                                                    </Typography>
                                                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                                        Source: {citation.citation_source}
                                                    </Typography>

                                                    {citation.pdf_url && (
                                                        <Button
                                                            size="small"
                                                            href={citation.pdf_url}
                                                            target="_blank"
                                                            sx={{ mt: 1, textTransform: 'none', padding: 0 }}
                                                        >
                                                            View Judgment PDF ↗
                                                        </Button>
                                                    )}
                                                </CardContent>
                                            </Card>
                                        </Grid>
                                    ))}
                                </Grid>
                            )}
                        </AccordionDetails>
                    </Accordion >
                </Box >
            )}
        </Box >
    );
};

export default PetitionDrafter;
