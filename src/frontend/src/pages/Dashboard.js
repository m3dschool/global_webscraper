import React from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useQuery } from 'react-query';
import { configsApi, resultsApi } from '../services/api';
import { format } from 'date-fns';

const Dashboard = () => {
  const { data: configs, isLoading: configsLoading, error: configsError } = useQuery(
    'configs',
    () => configsApi.getAll().then(res => res.data)
  );

  const { data: recentResults, isLoading: resultsLoading, error: resultsError } = useQuery(
    'recent-results',
    () => resultsApi.getAll(1, 10).then(res => res.data)
  );

  if (configsLoading || resultsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (configsError || resultsError) {
    return (
      <Container>
        <Alert severity="error">
          Failed to load dashboard data. Please try again.
        </Alert>
      </Container>
    );
  }

  const activeConfigs = configs?.filter(c => c.active) || [];
  const totalResults = recentResults?.total || 0;
  const successfulResults = recentResults?.results?.filter(r => r.status === 'success').length || 0;
  const successRate = totalResults > 0 ? ((successfulResults / totalResults) * 100).toFixed(1) : 0;

  const dashboardCards = [
    {
      title: 'Total Configs',
      value: configs?.length || 0,
      subtitle: `${activeConfigs.length} active`,
    },
    {
      title: 'Total Results',
      value: totalResults,
      subtitle: 'All time',
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      subtitle: 'Recent runs',
    },
    {
      title: 'Recent Runs',
      value: recentResults?.results?.length || 0,
      subtitle: 'Last 10 results',
    },
  ];

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {dashboardCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="h4" component="div">
                  {card.value}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {card.subtitle}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Active Configurations
            </Typography>
            {activeConfigs.length === 0 ? (
              <Typography color="textSecondary">
                No active configurations
              </Typography>
            ) : (
              <Box>
                {activeConfigs.slice(0, 5).map((config) => (
                  <Box
                    key={config.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                  >
                    <Typography variant="body2">{config.name}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {config.schedule_cron}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Results
            </Typography>
            {!recentResults?.results?.length ? (
              <Typography color="textSecondary">
                No recent results
              </Typography>
            ) : (
              <Box>
                {recentResults.results.slice(0, 5).map((result) => (
                  <Box
                    key={result.id}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 1,
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                  >
                    <Box>
                      <Typography variant="body2">
                        Config ID: {result.config_id}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {format(new Date(result.started_at), 'MMM dd, HH:mm')}
                      </Typography>
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: result.status === 'success' ? 'success.main' : 'error.main',
                        fontWeight: 'bold',
                      }}
                    >
                      {result.status.toUpperCase()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;