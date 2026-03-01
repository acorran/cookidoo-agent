import React from 'react';
import { Box, Button, Container, Typography, Grid, Card, CardContent } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Restaurant, Chat, ShoppingCart, AutoAwesome } from '@mui/icons-material';

const HomePage: React.FC = () => {
    const navigate = useNavigate();

    const features = [
        {
            title: 'Recipe Modification',
            description: 'Adapt any Cookidoo recipe to your dietary needs and preferences with AI-powered modifications.',
            icon: <Restaurant sx={{ fontSize: 60 }} />,
            path: '/recipes',
        },
        {
            title: 'Cooking Assistant',
            description: 'Ask questions, get cooking tips, and receive expert guidance powered by Claude AI.',
            icon: <Chat sx={{ fontSize: 60 }} />,
            path: '/chat',
        },
        {
            title: 'Smart Shopping Lists',
            description: 'Generate consolidated shopping lists from multiple recipes with automatic organization.',
            icon: <ShoppingCart sx={{ fontSize: 60 }} />,
            path: '/shopping-list',
        },
        {
            title: 'AI-Powered Intelligence',
            description: 'Backed by Databricks and Claude Sonnet 4.5 for intelligent recipe understanding.',
            icon: <AutoAwesome sx={{ fontSize: 60 }} />,
            path: '/',
        },
    ];

    return (
        <Container>
            <Box sx={{ my: 8, textAlign: 'center' }}>
                <Typography variant="h2" component="h1" gutterBottom>
                    Welcome to Cookidoo Agent Assistant
                </Typography>
                <Typography variant="h5" color="text.secondary" paragraph>
                    Transform your cooking experience with AI-powered recipe customization
                </Typography>
                <Button
                    variant="contained"
                    size="large"
                    onClick={() => navigate('/recipes')}
                    sx={{ mt: 3, mr: 2 }}
                >
                    Browse Recipes
                </Button>
                <Button
                    variant="outlined"
                    size="large"
                    onClick={() => navigate('/chat')}
                    sx={{ mt: 3 }}
                >
                    Chat with Assistant
                </Button>
            </Box>

            <Grid container spacing={4} sx={{ mt: 4 }}>
                {features.map((feature) => (
                    <Grid item xs={12} sm={6} md={3} key={feature.title}>
                        <Card
                            sx={{
                                height: '100%',
                                display: 'flex',
                                flexDirection: 'column',
                                cursor: 'pointer',
                                '&:hover': {
                                    boxShadow: 6,
                                    transform: 'translateY(-4px)',
                                    transition: 'all 0.3s',
                                },
                            }}
                            onClick={() => navigate(feature.path)}
                        >
                            <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                                <Box sx={{ color: 'primary.main', mb: 2 }}>
                                    {feature.icon}
                                </Box>
                                <Typography gutterBottom variant="h5" component="h2">
                                    {feature.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {feature.description}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            <Box sx={{ my: 8, textAlign: 'center', bgcolor: 'grey.100', p: 4, borderRadius: 2 }}>
                <Typography variant="h4" gutterBottom>
                    How It Works
                </Typography>
                <Grid container spacing={3} sx={{ mt: 2 }}>
                    <Grid item xs={12} md={4}>
                        <Typography variant="h6" gutterBottom>
                            1. Select a Recipe
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Browse and search through thousands of Cookidoo recipes
                        </Typography>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Typography variant="h6" gutterBottom>
                            2. Modify with AI
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Use natural language to request modifications - make it vegan, adjust servings, or change ingredients
                        </Typography>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Typography variant="h6" gutterBottom>
                            3. Cook & Enjoy
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Save your personalized recipe and get a ready-to-use shopping list
                        </Typography>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
};

export default HomePage;
