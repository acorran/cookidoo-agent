import React from 'react';
import { Box, Typography } from '@mui/material';

const ShoppingListPage: React.FC = () => {
    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Shopping List
            </Typography>
            <Typography variant="body1" color="text.secondary">
                Shopping list generation and management will be implemented here.
            </Typography>
            {/* TODO: Implement shopping list generation from recipes */}
        </Box>
    );
};

export default ShoppingListPage;
