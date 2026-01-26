import React from 'react';
import { Box, Card, CardContent, Typography, Chip, Tooltip, IconButton, Stack, Button } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import GavelIcon from '@mui/icons-material/Gavel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

export interface Citation {
    chunk_id: string;
    score: number;
    text: string;
    source: string;
    metadata: any;
}

interface CitationCardProps {
    citation: Citation;
    onCopy: (text: string) => void;
}

const CitationCard: React.FC<CitationCardProps> = ({ citation, onCopy }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const meta = citation.metadata || {};

    // Determine the type of document
    const isJudgment = meta.case_title || meta.document_type === 'judgment';
    const isAct = meta.act_name || meta.document_type === 'act';

    // Construct Display Fields
    const title = isJudgment
        ? `${meta.case_title} (${meta.year_of_judgment || 'Unknown Year'})`
        : isAct
            ? `${meta.act_name} - Section ${meta.section_id}`
            : citation.source;

    // Badges
    const court = meta.court_name;
    const outcome = meta.outcome;
    const winningParty = meta.winning_party;

    // Prioritize supporting_quote, then original_context, then raw text
    const contentText = meta.supporting_quote || meta.original_context || citation.text;

    // Outcome Color Logic
    let outcomeColor: "default" | "success" | "error" | "warning" = "default";
    if (outcome?.toLowerCase().includes("allowed") || outcome?.toLowerCase().includes("acquitted")) outcomeColor = "success";
    else if (outcome?.toLowerCase().includes("dismissed") || outcome?.toLowerCase().includes("convicted")) outcomeColor = "error";
    else if (outcome?.toLowerCase().includes("disposed")) outcomeColor = "warning";

    return (
        <Card variant="outlined" sx={{
            mb: 1.5,
            borderColor: 'divider',
            bgcolor: 'background.paper',
            '&:hover': { bgcolor: 'grey.50', borderColor: 'primary.light' },
            transition: 'all 0.2s ease-in-out'
        }}>
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>

                {/* Header Row */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <GavelIcon fontSize="small" color="primary" sx={{ opacity: 0.7 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.9rem', lineHeight: 1.2 }}>
                            {title}
                        </Typography>
                    </Box>
                    <Tooltip title="Copy Exact Text for Search (Ctrl+F)">
                        <IconButton
                            size="small"
                            onClick={() => onCopy(contentText)}
                            sx={{ mt: -0.5, mr: -0.5, color: 'text.secondary' }}
                        >
                            <ContentCopyIcon fontSize="small" sx={{ fontSize: '1rem' }} />
                        </IconButton>
                    </Tooltip>
                </Box>

                {/* Badges Row */}
                <Stack direction="row" spacing={1} sx={{ mb: 1.5 }} flexWrap="wrap" rowGap={1}>
                    {court && (
                        <Chip label={court} size="small" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
                    )}
                    {outcome && outcome !== "Unknown" && (
                        <Chip
                            label={outcome}
                            color={outcomeColor}
                            size="small"
                            sx={{ fontSize: '0.7rem', height: 20, fontWeight: 500 }}
                        />
                    )}
                    {meta.party_role && meta.party_role !== "None" && (
                        <Chip
                            icon={<InfoIcon sx={{ fontSize: '0.8rem !important' }} />}
                            label={`Role: ${meta.party_role}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                    )}
                    {winningParty && winningParty !== "None" && (
                        <Chip
                            icon={<CheckCircleIcon sx={{ fontSize: '0.8rem !important' }} />}
                            label={`Winner: ${winningParty}`}
                            color="success"
                            variant="outlined"
                            size="small"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                    )}
                    <Chip
                        label={`Match: ${(citation.score * 100).toFixed(0)}%`}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20, borderColor: 'transparent', color: 'text.secondary' }}
                    />
                </Stack>

                {/* Content Body */}
                <Box>
                    <Typography
                        variant="body2"
                        color="text.primary"
                        sx={{
                            fontSize: '0.85rem',
                            fontStyle: 'italic',
                            borderLeft: 3,
                            borderColor: 'primary.light',
                            pl: 1.5,
                            py: 0.5,
                            bgcolor: 'grey.50',
                            borderRadius: '0 4px 4px 0',
                            mb: 1
                        }}
                    >
                        {/* 
                            CLEANUP: The backend injects a metadata header for the LLM (e.g., "[CASE CONTEXT]... ---").
                            We strip this for the UI because we already show the metadata as chips/badges above.
                            We split by the separator "---" and take the last part.
                        */}
                        "{citation.text.includes("---") ? citation.text.split("---").pop()?.trim() : citation.text}"
                    </Typography>

                    {/* View Original Source Toggle */}
                    {meta.original_context && (
                        <Box>
                            <Button
                                size="small"
                                onClick={() => setIsExpanded(!isExpanded)}
                                startIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                sx={{ textTransform: 'none', fontSize: '0.75rem', p: 0, minWidth: 0, color: 'primary.main' }}
                            >
                                {isExpanded ? "Hide Original Source" : "View Original Source"}
                            </Button>

                            {isExpanded && (
                                <Box sx={{
                                    mt: 1,
                                    p: 1.5,
                                    bgcolor: '#fff8e1', // Light yellow background
                                    border: '1px solid #ffe0b2',
                                    borderRadius: 1,
                                    fontSize: '0.8rem',
                                    color: 'text.secondary',
                                    whiteSpace: 'pre-wrap' // Preserve formatting
                                }}>
                                    <Typography variant="caption" display="block" sx={{ fontWeight: 600, mb: 0.5, color: 'warning.dark' }}>
                                        Original PDF Text (Verbatim):
                                    </Typography>
                                    {/* Highlight the supporting quote within the original context */}
                                    {meta.original_context.split(meta.supporting_quote || "").map((part: string, index: number, array: string[]) => (
                                        <React.Fragment key={index}>
                                            {part}
                                            {index < array.length - 1 && (
                                                <span style={{ backgroundColor: '#ffeb3b', fontWeight: 'bold', color: 'black' }}>
                                                    {meta.supporting_quote}
                                                </span>
                                            )}
                                        </React.Fragment>
                                    ))}
                                </Box>
                            )}
                        </Box>
                    )}
                </Box>
            </CardContent>
        </Card>
    );
};

export default CitationCard;
