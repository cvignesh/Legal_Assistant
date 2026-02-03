import React, { useState, useEffect, useRef } from 'react';
import { Box, IconButton, Paper, Typography, TextField, Tooltip, CircularProgress, Button, Chip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ClearIcon from '@mui/icons-material/ClearAll';
import AddIcon from '@mui/icons-material/Add';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import WarningIcon from '@mui/icons-material/Warning';
import SecurityIcon from '@mui/icons-material/Security';
import CitationCard from './ChatBot/CitationCard';
import SourceCard, { GroupedSource } from './ChatBot/SourceCard';

interface Citation {
    chunk_id: string;
    score: number;
    text: string;
    source: string;
    metadata: any;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
    sources?: GroupedSource[];
    guardrail_actions?: string[];
    timestamp: Date;
}

const ChatAssistantPage: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Create session on mount
    useEffect(() => {
        const createSession = async () => {
            try {
                console.log('[ChatAssistantPage] Creating session...');
                const response = await fetch('http://localhost:8000/api/chat/session');
                const data = await response.json();
                console.log('[ChatAssistantPage] Session created:', data.session_id);
                setSessionId(data.session_id);
            } catch (error) {
                console.error('[ChatAssistantPage] Failed to create session:', error);
            }
        };
        createSession();
    }, []);

    const handleSend = async () => {
        console.log('[ChatAssistantPage] handleSend called', { input: input.trim(), sessionId, isLoading });

        if (!input.trim() || !sessionId || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: userMessage.content,
                }),
            });

            const data = await response.json();
            console.log('[ChatAssistantPage] Received response:', data);

            const assistantMessage: Message = {
                role: 'assistant',
                content: data.answer,
                citations: data.citations,
                sources: data.sources,
                guardrail_actions: data.guardrail_actions,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClear = async () => {
        if (!sessionId) return;
        try {
            await fetch(`http://localhost:8000/api/chat/session/${sessionId}`, {
                method: 'DELETE',
            });
            setMessages([]);
        } catch (error) {
            console.error('Failed to clear session:', error);
        }
    };

    const handleNewChat = async () => {
        try {
            // Clear current session
            if (sessionId) {
                await fetch(`http://localhost:8000/api/chat/session/${sessionId}`, {
                    method: 'DELETE',
                });
            }
            // Create brand new session
            const response = await fetch('http://localhost:8000/api/chat/session');
            const data = await response.json();
            setSessionId(data.session_id);
            setMessages([]);
            console.log('[ChatAssistantPage] New chat started:', data.session_id);
        } catch (error) {
            console.error('Failed to start new chat:', error);
        }
    };

    const copyCitation = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <Box
            sx={{
                height: 'calc(100vh - 200px)',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'background.paper',
                borderRadius: 2,
                overflow: 'hidden',
                boxShadow: 2,
            }}
        >
            {/* Header */}
            <Box
                sx={{
                    p: 2,
                    bgcolor: 'primary.main',
                    color: 'white',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}
            >
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    Legal Assistant Chat
                </Typography>
                <Box>
                    <Tooltip title="New Chat">
                        <Button
                            variant="contained"
                            size="small"
                            onClick={handleNewChat}
                            startIcon={<AddIcon />}
                            sx={{
                                bgcolor: 'rgba(255, 255, 255, 0.2)',
                                color: 'white',
                                mr: 1,
                                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' },
                            }}
                        >
                            New Chat
                        </Button>
                    </Tooltip>
                    <Tooltip title="Clear Conversation">
                        <Button
                            variant="contained"
                            size="small"
                            onClick={handleClear}
                            startIcon={<ClearIcon />}
                            sx={{
                                bgcolor: 'rgba(255, 255, 255, 0.2)',
                                color: 'white',
                                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' },
                            }}
                        >
                            Clear
                        </Button>
                    </Tooltip>
                </Box>
            </Box>

            {/* Messages Area */}
            <Box
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    p: 3,
                    bgcolor: '#f8f9fa',
                }}
            >
                {messages.length === 0 && (
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            gap: 2,
                        }}
                    >
                        <Typography variant="h4" color="text.secondary" sx={{ fontWeight: 300 }}>
                            👋 Welcome to Legal Assistant
                        </Typography>
                        <Typography variant="body1" color="text.secondary" align="center">
                            Ask me anything about Indian laws, judgments, and legal matters.
                            <br />
                            I'll provide detailed answers with relevant citations and sources.
                        </Typography>
                    </Box>
                )}

                {messages.map((msg, idx) => (
                    <Box key={idx} sx={{ mb: 3 }}>
                        {msg.role === 'user' ? (
                            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <Paper
                                    elevation={1}
                                    sx={{
                                        p: 2,
                                        bgcolor: 'primary.main',
                                        color: 'white',
                                        maxWidth: '70%',
                                        borderRadius: 2,
                                    }}
                                >
                                    <Typography variant="body1">{msg.content}</Typography>
                                </Paper>
                            </Box>
                        ) : (
                            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                                <Paper
                                    elevation={1}
                                    sx={{
                                        p: 2,
                                        bgcolor: 'white',
                                        maxWidth: '85%',
                                        borderRadius: 2,
                                    }}
                                >
                                    <Typography variant="body1" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
                                        {msg.content}
                                    </Typography>

                                    {/* Guardrails Badges */}
                                    {msg.guardrail_actions && msg.guardrail_actions.length > 0 && (
                                        <Box sx={{ mt: 1, mb: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {msg.guardrail_actions.map((action, aidx) => {
                                                let color: "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" = "default";
                                                let icon = <SecurityIcon fontSize="small" />;

                                                if (action.includes("Blocked") || action.includes("Violation") || action.includes("Safety") || action.includes("Injection")) {
                                                    color = "error";
                                                    icon = <WarningIcon fontSize="small" />;
                                                }
                                                else if (action.includes("Redacted")) color = "warning";
                                                else if (action.includes("Verified") || action.includes("Citation")) {
                                                    color = "success";
                                                    icon = <VerifiedUserIcon fontSize="small" />;
                                                }

                                                return (
                                                    <Chip
                                                        key={aidx}
                                                        label={action}
                                                        size="small"
                                                        color={color}
                                                        icon={icon}
                                                        variant="outlined"
                                                    />
                                                );
                                            })}
                                        </Box>
                                    )}

                                    {/* Sources Section */}
                                    {(msg.sources && msg.sources.length > 0) ? (
                                        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                            <Typography
                                                variant="subtitle2"
                                                color="text.secondary"
                                                sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 0.5, fontWeight: 600 }}
                                            >
                                                ⚖️ Sources ({msg.sources.length})
                                            </Typography>
                                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                {msg.sources.map((source, sidx) => (
                                                    <SourceCard
                                                        key={sidx}
                                                        source={source}
                                                        onCopy={(text) => copyCitation(text)}
                                                    />
                                                ))}
                                            </Box>
                                        </Box>
                                    ) : (msg.citations && msg.citations.length > 0) && (
                                        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                            <Typography
                                                variant="subtitle2"
                                                color="text.secondary"
                                                sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 0.5, fontWeight: 600 }}
                                            >
                                                ⚖️ Legal Sources ({msg.citations.length})
                                            </Typography>
                                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                {msg.citations.map((citation, cidx) => (
                                                    <CitationCard
                                                        key={cidx}
                                                        citation={citation}
                                                        onCopy={(text) => copyCitation(text)}
                                                    />
                                                ))}
                                            </Box>
                                        </Box>
                                    )}
                                </Paper>
                            </Box>
                        )}
                    </Box>
                ))}

                {isLoading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Analyzing your query and searching legal database...
                        </Typography>
                    </Box>
                )}

                <div ref={messagesEndRef} />
            </Box>

            {/* Input Area */}
            <Box
                sx={{
                    p: 2,
                    borderTop: 1,
                    borderColor: 'divider',
                    bgcolor: 'background.paper',
                }}
            >
                <Box sx={{ display: 'flex', gap: 2, maxWidth: 1200, mx: 'auto' }}>
                    <TextField
                        fullWidth
                        multiline
                        maxRows={4}
                        placeholder="Ask about laws, sections, cases, judgments..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        disabled={isLoading}
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                borderRadius: 2,
                            },
                        }}
                    />
                    <IconButton
                        color="primary"
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        sx={{
                            bgcolor: 'primary.main',
                            color: 'white',
                            width: 56,
                            height: 56,
                            '&:hover': { bgcolor: 'primary.dark' },
                            '&:disabled': { bgcolor: 'grey.300' },
                        }}
                    >
                        <SendIcon />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
};

export default ChatAssistantPage;
