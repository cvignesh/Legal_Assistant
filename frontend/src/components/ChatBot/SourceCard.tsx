import React, { useState } from 'react';
import { Box, Card, CardContent, Typography, Chip, Tooltip, IconButton, Stack, Button, Collapse, Link } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import GavelIcon from '@mui/icons-material/Gavel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

// Interface matching the backend GroupedSource model
export interface GroupedSource {
    id: string;
    title: string;
    doc_url?: string;
    metadata: any;
    chunks: any[]; // List of Citations
}

interface SourceCardProps {
    source: GroupedSource;
    onCopy: (text: string) => void;
}

const SourceCard: React.FC<SourceCardProps> = ({ source, onCopy }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const meta = source.metadata || {};

    // Badges
    const court = meta.court_name;
    const outcome = meta.outcome;
    const winningParty = meta.winning_party;

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
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                        <GavelIcon fontSize="small" color="primary" sx={{ opacity: 0.7 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '0.9rem', lineHeight: 1.2 }}>
                            {source.title}
                        </Typography>
                    </Box>

                    {/* Actions */}
                    <Stack direction="row" spacing={0.5}>
                        {source.doc_url && (
                            <Tooltip title="View Original PDF">
                                <Button
                                    size="small"
                                    component={Link}
                                    href={source.doc_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    startIcon={<OpenInNewIcon sx={{ fontSize: '0.8rem !important' }} />}
                                    sx={{
                                        minWidth: 0,
                                        px: 1,
                                        fontSize: '0.75rem',
                                        textTransform: 'none',
                                        color: 'primary.main'
                                    }}
                                >
                                    View PDF
                                </Button>
                            </Tooltip>
                        )}
                    </Stack>
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
                    {/* Role Chip if relevant */}
                    {meta.party_role && meta.party_role !== "None" && (
                        <Chip
                            icon={<InfoIcon sx={{ fontSize: '0.8rem !important' }} />}
                            label={`Role: ${meta.party_role}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                    )}
                </Stack>

                {/* Collapsible Excerpts */}
                <Box>
                    <Button
                        size="small"
                        onClick={() => setIsExpanded(!isExpanded)}
                        endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        sx={{
                            textTransform: 'none',
                            fontSize: '0.8rem',
                            p: 0,
                            minWidth: 0,
                            color: 'text.secondary',
                            mb: isExpanded ? 1 : 0
                        }}
                    >
                        {isExpanded ? "Hide Excerpts" : `View ${source.chunks.length} Relevant Excerpts`}
                    </Button>

                    <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <Stack spacing={1} sx={{ mt: 1 }}>
                            {source.chunks.map((chunk, idx) => (
                                <Box key={idx} sx={{
                                    p: 1,
                                    bgcolor: 'grey.50',
                                    borderRadius: 1,
                                    border: '1px solid',
                                    borderColor: 'grey.200',
                                    position: 'relative'
                                }}>
                                    {/* Copy Button for Chunk */}
                                    <Tooltip title="Copy Text">
                                        <IconButton
                                            size="small"
                                            onClick={() => onCopy(chunk.text)}
                                            sx={{ position: 'absolute', top: 2, right: 2, p: 0.5 }}
                                        >
                                            <ContentCopyIcon sx={{ fontSize: '0.9rem' }} />
                                        </IconButton>
                                    </Tooltip>

                                    <Typography variant="body2" sx={{ fontSize: '0.85rem', fontStyle: 'italic', pr: 3 }}>
                                        "{chunk.text.includes("---") ? chunk.text.split("---").pop()?.trim() : chunk.text}"
                                    </Typography>

                                    {/* Match Score */}
                                    <Box sx={{ mt: 0.5, display: 'flex', justifyContent: 'flex-end' }}>
                                        <Typography variant="caption" color="text.secondary">
                                            Match: {(chunk.score * 100).toFixed(0)}%
                                        </Typography>
                                    </Box>
                                </Box>
                            ))}
                        </Stack>
                    </Collapse>
                </Box>

            </CardContent>
        </Card>
    );
};

export default SourceCard;
