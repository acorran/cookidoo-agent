import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './App.css';

// Components (to be created)
import HomePage from './pages/HomePage';
import RecipesPage from './pages/RecipesPage';
import ChatPage from './pages/ChatPage';
import ShoppingListPage from './pages/ShoppingListPage';
import Layout from './components/Layout';

// Create theme
const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
    },
});

// Create query client for React Query
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <Router>
                    <Layout>
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/recipes" element={<RecipesPage />} />
                            <Route path="/recipes/:id" element={<RecipesPage />} />
                            <Route path="/chat" element={<ChatPage />} />
                            <Route path="/shopping-list" element={<ShoppingListPage />} />
                        </Routes>
                    </Layout>
                </Router>
            </ThemeProvider>
        </QueryClientProvider>
    );
}

export default App;
