import React, { useState, useEffect, useRef } from 'react';
import { Box, IconButton, Paper, Typography, TextField, Stack, Chip, Tooltip, CircularProgress } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import ClearIcon from '@mui/icons-material/ClearAll';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AddIcon from '@mui/icons-material/Add';

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
    timestamp: Date;
}

const ChatBot: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
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
                console.log('[ChatBot] Creating session...');
                const response = await fetch('http://localhost:8000/api/chat/session');
                const data = await response.json();
                console.log('[ChatBot] Session created:', data.session_id);
                setSessionId(data.session_id);
            } catch (error) {
                console.error('[ChatBot] Failed to create session:', error);
            }
        };
        createSession();
    }, []);

    const handleSend = async () => {
        console.log('[ChatBot] handleSend called', { input: input.trim(), sessionId, isLoading });

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

            const assistantMessage: Message = {
                role: 'assistant',
                content: data.answer,
                citations: data.citations,
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
            console.log('[ChatBot] New chat started:', data.session_id);
        } catch (error) {
            console.error('Failed to start new chat:', error);
        }
    };

    const copyCitation = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <>
            {/* Floating Chat Icon */}
            {!isOpen && (
                <IconButton
                    onClick={() => setIsOpen(true)}
                    sx={{
                        position: 'fixed',
                        bottom: 24,
                        right: 24,
                        width: 60,
                        height: 60,
                        bgcolor: 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: 'primary.dark' },
                        boxShadow: 4,
                        zIndex: 1000,
                    }}
                >
                    <ChatIcon fontSize="large" />
                </IconButton>
            )}

            {/* Chat Window */}
            {isOpen && (
                <Paper
                    elevation={8}
                    sx={{
                        position: 'fixed',
                        bottom: 24,
                        right: 24,
                        width: 400,
                        height: 600,
                        display: 'flex',
                        flexDirection: 'column',
                        zIndex: 1000,
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
                        <Typography variant="h6">Legal Assistant</Typography>
                        <Box>
                            <Tooltip title="New Chat">
                                <IconButton size="small" onClick={handleNewChat} sx={{ color: 'white', mr: 1 }}>
                                    <AddIcon />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Clear Conversation">
                                <IconButton size="small" onClick={handleClear} sx={{ color: 'white', mr: 1 }}>
                                    <ClearIcon />
                                </IconButton>
                            </Tooltip>
                            <IconButton size="small" onClick={() => setIsOpen(false)} sx={{ color: 'white' }}>
                                <CloseIcon />
                            </IconButton>
                        </Box>
                    </Box>

                    {/* Messages */}
                    <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
                        {messages.length === 0 && (
                            <Typography variant="body2" color="text.secondary" align="center">
                                Ask me anything about Indian laws and judgments!
                            </Typography>
                        )}

                        {messages.map((msg, idx) => (
                            <Box key={idx} sx={{ mb: 2 }}>
                                {msg.role === 'user' ? (
                                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                                        <Paper
                                            sx={{
                                                p: 1.5,
                                                bgcolor: 'primary.light',
                                                color: 'white',
                                                maxWidth: '80%',
                                            }}
                                        >
                                            <Typography variant="body2">{msg.content}</Typography>
                                        </Paper>
                                    </Box>
                                ) : (
                                    <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                                        <Paper sx={{ p: 1.5, bgcolor: 'grey.100', maxWidth: '80%' }}>
                                            <Typography variant="body2" sx={{ mb: 1 }}>
                                                {msg.content}
                                            </Typography>

                                            {msg.citations && msg.citations.filter(c => c.score > 0.1).length > 0 && (
                                                <Box sx={{ mt: 1 }}>
                                                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                                                        📎 Sources:
                                                    </Typography>
                                                    <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5 }}>
                                                        {msg.citations
                                                            .filter(c => c.score > 0.1)
                                                            .map((citation, cidx) => (
                                                                <Tooltip key={cidx} title={`${citation.text.substring(0, 100)}...`}>
                                                                    <Chip
                                                                        label={`${citation.source.substring(0, 30)} (${citation.score.toFixed(2)})`}
                                                                        size="small"
                                                                        onClick={() => copyCitation(citation.text)}
                                                                        icon={<ContentCopyIcon fontSize="small" />}
                                                                        sx={{ fontSize: '0.7rem', height: 'auto', py: 0.5 }}
                                                                    />
                                                                </Tooltip>
                                                            ))}
                                                    </Stack>
                                                </Box>
                                            )}
                                        </Paper>
                                    </Box>
                                )}
                            </Box>
                        ))}

                        {isLoading && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <CircularProgress size={16} />
                                <Typography variant="body2" color="text.secondary">
                                    Thinking...
                                </Typography>
                            </Box>
                        )}

                        <div ref={messagesEndRef} />
                    </Box>

                    {/* Input */}
                    <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <TextField
                                fullWidth
                                size="small"
                                placeholder="Ask about laws, sections, cases..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                                disabled={isLoading}
                            />
                            <IconButton
                                color="primary"
                                onClick={handleSend}
                                disabled={!input.trim() || isLoading}
                            >
                                <SendIcon />
                            </IconButton>
                        </Box>
                    </Box>
                </Paper>
            )}
        </>
    );
};

export default ChatBot;
