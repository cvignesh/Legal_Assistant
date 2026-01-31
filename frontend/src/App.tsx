import { useState } from 'react';
import { Box, Tabs, Tab, AppBar, Toolbar, Typography, Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import IngestionPage from './components/IngestionPage';
import ChatBot from './components/ChatBot';
import ViabilityPredictor from './components/ViabilityPredictor';

const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
        },
        background: {
            default: '#f5f5f5',
        },
    },
});

function TabPanel(props: { children?: React.ReactNode; index: number; value: number }) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

function App() {
    const [value, setValue] = useState(0);

    const handleChange = (event: React.SyntheticEvent, newValue: number) => {
        setValue(newValue);
    };

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ flexGrow: 1 }}>
                <AppBar position="static">
                    <Toolbar>
                        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                            Legal Assistant AI
                        </Typography>
                    </Toolbar>
                    <Tabs value={value} onChange={handleChange} indicatorColor="secondary" textColor="inherit" centered>
                        <Tab label="Ingestion" />
                        <Tab label="Chat Assistant" />
                        <Tab label="Viability Predictor" />
                    </Tabs>
                </AppBar>

                <Container maxWidth="xl" sx={{ mt: 4 }}>
                    <TabPanel value={value} index={0}>
                        <IngestionPage />
                    </TabPanel>
                    <TabPanel value={value} index={1}>
                        <ChatBot />
                    </TabPanel>
                    <TabPanel value={value} index={2}>
                        <ViabilityPredictor />
                    </TabPanel>
                </Container>
            </Box>
        </ThemeProvider>
    );
}

export default App;
