import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    CardMedia,
    Grid,
    Chip,
    CircularProgress,
    Alert,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    List,
    ListItem,
    ListItemText,
    Tabs,
    Tab,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import { recipeApi } from '../services/api';

interface CollectionRecipe {
    id: string;
    name: string;
    total_time_minutes: number | null;
}

interface Collection {
    id: string;
    name: string;
    description: string;
    recipes: CollectionRecipe[];
}

interface CreatedRecipe {
    id: string;
    name: string;
    has_image: boolean;
    image_url: string;
    total_time_minutes: number | null;
}

const RecipesPage: React.FC = () => {
    const [tab, setTab] = useState(0);
    const [collections, setCollections] = useState<Collection[]>([]);
    const [createdRecipes, setCreatedRecipes] = useState<CreatedRecipe[]>([]);
    const [totalCollectionRecipes, setTotalCollectionRecipes] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const [collRes, createdRes] = await Promise.all([
                    recipeApi.getCollections(),
                    recipeApi.getCreatedRecipes(),
                ]);
                setCollections(collRes.data.collections || []);
                setTotalCollectionRecipes(collRes.data.total_recipes || 0);
                setCreatedRecipes(createdRes.data.recipes || []);
            } catch (err: unknown) {
                const error = err as { response?: { data?: { detail?: string } }; message?: string };
                const msg =
                    error?.response?.data?.detail ||
                    error?.message ||
                    'Failed to load recipes';
                setError(msg);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Loading recipes from Cookidoo...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 2 }}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: { xs: 1, md: 3 } }}>
            <Typography variant="h4" gutterBottom>
                <MenuBookIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                My Recipes
            </Typography>

            <Tabs
                value={tab}
                onChange={(_, v) => setTab(v)}
                sx={{ mb: 3 }}
                indicatorColor="primary"
            >
                <Tab
                    label={`Collections (${collections.length})`}
                    icon={<RestaurantIcon />}
                    iconPosition="start"
                />
                <Tab
                    label={`Created Recipes (${createdRecipes.length})`}
                    icon={<MenuBookIcon />}
                    iconPosition="start"
                />
            </Tabs>

            {/* ── Collections tab ─────────────────────────────── */}
            {tab === 0 && (
                <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {totalCollectionRecipes} recipes across {collections.length} collections
                    </Typography>
                    {collections.map((coll) => (
                        <Accordion key={coll.id} defaultExpanded={coll.recipes.length <= 6}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                                    {coll.name}
                                </Typography>
                                <Chip
                                    label={`${coll.recipes.length} recipe${coll.recipes.length !== 1 ? 's' : ''}`}
                                    size="small"
                                    color="primary"
                                    variant="outlined"
                                    sx={{ mr: 1 }}
                                />
                            </AccordionSummary>
                            <AccordionDetails>
                                <List dense disablePadding>
                                    {coll.recipes.map((r) => (
                                        <ListItem key={r.id} divider>
                                            <ListItemText
                                                primary={r.name}
                                                secondary={
                                                    r.total_time_minutes
                                                        ? `${r.total_time_minutes} min`
                                                        : undefined
                                                }
                                            />
                                            {r.total_time_minutes && (
                                                <Chip
                                                    icon={<AccessTimeIcon />}
                                                    label={`${r.total_time_minutes} min`}
                                                    size="small"
                                                    variant="outlined"
                                                />
                                            )}
                                        </ListItem>
                                    ))}
                                    {coll.recipes.length === 0 && (
                                        <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{ py: 1 }}
                                        >
                                            No recipes in this collection
                                        </Typography>
                                    )}
                                </List>
                            </AccordionDetails>
                        </Accordion>
                    ))}
                    {collections.length === 0 && (
                        <Alert severity="info">No custom collections found.</Alert>
                    )}
                </Box>
            )}

            {/* ── Created Recipes tab ────────────────────────── */}
            {tab === 1 && (
                <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {createdRecipes.length} recipes you&apos;ve created or imported
                    </Typography>
                    <Grid container spacing={2}>
                        {createdRecipes.map((recipe) => (
                            <Grid item xs={12} sm={6} md={4} lg={3} key={recipe.id}>
                                <Card
                                    sx={{
                                        height: '100%',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        '&:hover': {
                                            boxShadow: 4,
                                            cursor: 'pointer',
                                        },
                                    }}
                                >
                                    {recipe.has_image && recipe.image_url ? (
                                        <CardMedia
                                            component="img"
                                            height="180"
                                            image={recipe.image_url}
                                            alt={recipe.name}
                                            sx={{ objectFit: 'cover' }}
                                        />
                                    ) : (
                                        <Box
                                            sx={{
                                                height: 180,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                bgcolor: 'grey.100',
                                            }}
                                        >
                                            <RestaurantIcon
                                                sx={{ fontSize: 60, color: 'grey.400' }}
                                            />
                                        </Box>
                                    )}
                                    <CardContent sx={{ flexGrow: 1 }}>
                                        <Typography variant="subtitle1" gutterBottom noWrap>
                                            {recipe.name}
                                        </Typography>
                                        {recipe.total_time_minutes && (
                                            <Chip
                                                icon={<AccessTimeIcon />}
                                                label={`${recipe.total_time_minutes} min`}
                                                size="small"
                                                variant="outlined"
                                            />
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                    {createdRecipes.length === 0 && (
                        <Alert severity="info">
                            No created recipes found. Use the agent to create your first recipe!
                        </Alert>
                    )}
                </Box>
            )}
        </Box>
    );
};

export default RecipesPage;
