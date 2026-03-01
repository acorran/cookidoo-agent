import React from 'react';
import { Box, Typography } from '@mui/material';

const ChatPage: React.FC = () => {
    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Chat Assistant
            </Typography>
            <Typography variant="body1" color="text.secondary">
                AI-powered cooking assistant chat interface will be implemented here.
            </Typography>
            {/* TODO: Implement chat interface with message history and input */}
        </Box>
    );
};

export default ChatPage;
