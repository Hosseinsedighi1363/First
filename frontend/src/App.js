import React from 'react';
import Layout from './components/Layout';
import { Typography } from '@mui/material';

function App() {
  return (
    <Layout>
      <Typography variant="h4" component="h1" gutterBottom>
        Student Dashboard
      </Typography>
      <Typography paragraph>
        Welcome to your dashboard. Here you can see your assignments, quizzes, and profile.
      </Typography>
    </Layout>
  );
}

export default App;