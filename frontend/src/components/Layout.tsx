import React from 'react';
import {
    AppBar,
    Box,
    Container,
    Drawer,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Toolbar,
    Typography,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Home,
    Restaurant,
    Chat,
    ShoppingCart,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const [drawerOpen, setDrawerOpen] = React.useState(false);
    const navigate = useNavigate();

    const menuItems = [
        { text: 'Home', icon: <Home />, path: '/' },
        { text: 'Recipes', icon: <Restaurant />, path: '/recipes' },
        { text: 'Chat Assistant', icon: <Chat />, path: '/chat' },
        { text: 'Shopping List', icon: <ShoppingCart />, path: '/shopping-list' },
    ];

    const handleDrawerToggle = () => {
        setDrawerOpen(!drawerOpen);
    };

    const handleNavigation = (path: string) => {
        navigate(path);
        setDrawerOpen(false);
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <AppBar position="static">
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Cookidoo Agent Assistant
                    </Typography>
                </Toolbar>
            </AppBar>

            <Drawer anchor="left" open={drawerOpen} onClose={handleDrawerToggle}>
                <Box sx={{ width: 250 }} role="presentation">
                    <List>
                        {menuItems.map((item) => (
                            <ListItem key={item.text} disablePadding>
                                <ListItemButton onClick={() => handleNavigation(item.path)}>
                                    <ListItemIcon>{item.icon}</ListItemIcon>
                                    <ListItemText primary={item.text} />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </List>
                </Box>
            </Drawer>

            <Container component="main" sx={{ flex: 1, py: 4 }}>
                {children}
            </Container>

            <Box
                component="footer"
                sx={{
                    py: 3,
                    px: 2,
                    mt: 'auto',
                    backgroundColor: (theme) => theme.palette.grey[200],
                }}
            >
                <Container maxWidth="sm">
                    <Typography variant="body2" color="text.secondary" align="center">
                        © 2025 Cookidoo Agent Assistant. Powered by Databricks & Claude.
                    </Typography>
                </Container>
            </Box>
        </Box>
    );
};

export default Layout;
