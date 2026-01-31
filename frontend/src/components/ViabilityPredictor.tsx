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
    Chip,
    Divider
} from '@mui/material';
import { Gavel, TrendingUp, TrendingDown, HelpOutline } from '@mui/icons-material';
import { viabilityAPI } from '../api';
import { PredictionResult, Precedent } from '../types';

const COURTS = [
    "All Courts",
    "Supreme Court of India",
    "Delhi High Court",
    "Bombay High Court",
    "Allahabad High Court",
    "Karnataka High Court",
    "Madras High Court"
];

const ViabilityPredictor: React.FC = () => {
    // State
    const [facts, setFacts] = useState('');
    const [role, setRole] = useState('Petitioner');
    const [court, setCourt] = useState('All Courts');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PredictionResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handlePredict = async () => {
        if (!facts.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const data = await viabilityAPI.predict(facts, role, court);
            setResult(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to generate prediction");
        } finally {
            setLoading(false);
        }
    };

    // Helper: Gauge Color
    const getGaugeColor = (score: number) => {
        if (score >= 70) return '#4caf50'; // Green
        if (score <= 40) return '#f44336'; // Red
        return '#ff9800'; // Orange
    };

    // Helper: Outcome Chip
    const getOutcomeColor = (outcome: string) => {
        outcome = outcome.toLowerCase();
        if (outcome.includes('allowed') || outcome.includes('acquitted')) return 'success';
        if (outcome.includes('dismissed') || outcome.includes('convicted')) return 'error';
        return 'warning';
    };

    return (
        <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUp /> Viability Predictor
            </Typography>
            <Typography variant="subtitle1" color="text.secondary" paragraph>
                Predict your case's winning probability based on AI analysis of similar historical judgments.
            </Typography>

            {/* Input Section */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <TextField
                            label="Case Facts"
                            multiline
                            rows={4}
                            fullWidth
                            value={facts}
                            onChange={(e) => setFacts(e.target.value)}
                            placeholder="Describe your situation (e.g., 'Cheque bounced due to signature mismatch...')"
                            variant="outlined"
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                            <InputLabel>Your Role</InputLabel>
                            <Select
                                value={role}
                                label="Your Role"
                                onChange={(e) => setRole(e.target.value)}
                            >
                                <MenuItem value="Petitioner">Petitioner / Complainant</MenuItem>
                                <MenuItem value="Respondent">Respondent / Accused</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                            <InputLabel>Target Court</InputLabel>
                            <Select
                                value={court}
                                label="Target Court"
                                onChange={(e) => setCourt(e.target.value)}
                            >
                                {COURTS.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <Button
                            variant="contained"
                            size="large"
                            onClick={handlePredict}
                            disabled={loading || !facts}
                            startIcon={loading ? <CircularProgress size={20} /> : <Gavel />}
                            fullWidth
                        >
                            {loading ? "Analyzing Precedents..." : "Analyze Viability"}
                        </Button>
                        {error && (
                            <Typography color="error" sx={{ mt: 2 }}>
                                {error}
                            </Typography>
                        )}
                    </Grid>
                </Grid>
            </Paper>

            {/* Results Section */}
            {result && (
                <Box>
                    {/* Gauge & Summary */}
                    <Paper elevation={3} sx={{ p: 4, mb: 4, textAlign: 'center', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
                        <Grid container alignItems="center" spacing={4}>
                            <Grid item xs={12} md={4}>
                                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                    <CircularProgress
                                        variant="determinate"
                                        value={result.viability_score}
                                        size={120}
                                        thickness={5}
                                        sx={{ color: getGaugeColor(result.viability_score) }}
                                    />
                                    <Box
                                        sx={{
                                            top: 0,
                                            left: 0,
                                            bottom: 0,
                                            right: 0,
                                            position: 'absolute',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexDirection: 'column'
                                        }}
                                    >
                                        <Typography variant="h4" component="div" color="text.secondary">
                                            {Math.round(result.viability_score)}%
                                        </Typography>
                                    </Box>
                                </Box>
                                <Typography variant="h6" sx={{ mt: 2, fontWeight: 'bold' }}>
                                    {result.viability_label} Viability
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={8} sx={{ textAlign: 'left' }}>
                                <Typography variant="h6" gutterBottom>
                                    Strategic Analysis
                                </Typography>
                                <Typography variant="body1" paragraph>
                                    {result.strategic_advice}
                                </Typography>
                                <Typography variant="caption" display="block" color="text.secondary">
                                    Analyzed {result.total_analyzed} similar cases ({result.favorable_count} favorable).
                                </Typography>
                            </Grid>
                        </Grid>
                    </Paper>

                    {/* Precedents Carousel (Grid for now) */}
                    <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                        Top 5 Key Precedents
                    </Typography>
                    <Grid container spacing={3}>
                        {result.top_precedents.map((precedent, index) => (
                            <Grid item xs={12} md={6} key={index}>
                                <Card variant="outlined" sx={{ height: '100%' }}>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Chip
                                                label={precedent.outcome}
                                                color={getOutcomeColor(precedent.outcome) as any}
                                                size="small"
                                            />
                                            <Typography variant="caption" color="text.secondary">
                                                Sim: {(precedent.score * 100).toFixed(0)}%
                                            </Typography>
                                        </Box>
                                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                                            {precedent.case_title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            {precedent.court} ({precedent.year})
                                        </Typography>
                                        <Divider sx={{ my: 1 }} />
                                        <Typography variant="body2" sx={{ fontStyle: 'italic', bgcolor: '#f9f9f9', p: 1, borderRadius: 1 }}>
                                            "{precedent.snippet}"
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Box>
            )}
        </Box>
    );
};

export default ViabilityPredictor;
