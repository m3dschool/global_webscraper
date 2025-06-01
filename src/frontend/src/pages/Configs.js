import React, { useState } from 'react';
import {
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as RunIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useForm, Controller } from 'react-hook-form';
import { configsApi, jobsApi } from '../services/api';
import { format } from 'date-fns';

const Configs = () => {
  const [openDialog, setOpenDialog] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  
  const queryClient = useQueryClient();
  
  const { control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      start_url: '',
      css_selector: '',
      region: 'US',
      proxy_enabled: false,
      schedule_cron: '0 * * * *',
      gemini_prompt: '',
      gemini_model: 'gemini-pro',
      active: true,
      wait_time: 5,
      max_retries: 3,
      timeout: 30,
    },
  });

  const { data: configs, isLoading, error } = useQuery(
    'configs',
    () => configsApi.getAll().then(res => res.data)
  );

  const createMutation = useMutation(configsApi.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('configs');
      setOpenDialog(false);
      reset();
    },
  });

  const updateMutation = useMutation(
    ({ id, data }) => configsApi.update(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('configs');
        setOpenDialog(false);
        setEditingConfig(null);
        reset();
      },
    }
  );

  const deleteMutation = useMutation(configsApi.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries('configs');
      setDeleteConfirm(null);
    },
  });

  const runJobMutation = useMutation(jobsApi.trigger, {
    onSuccess: () => {
      // Could show a success message here
      console.log('Job triggered successfully');
    },
  });

  const handleCreateEdit = (data) => {
    if (editingConfig) {
      updateMutation.mutate({ id: editingConfig.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    reset(config);
    setOpenDialog(true);
  };

  const handleDelete = (id) => {
    deleteMutation.mutate(id);
  };

  const handleRunJob = (configId) => {
    runJobMutation.mutate(configId);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error">
          Failed to load configurations. Please try again.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Scrape Configurations
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingConfig(null);
            reset();
            setOpenDialog(true);
          }}
        >
          Add Config
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Schedule</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {configs?.map((config) => (
              <TableRow key={config.id}>
                <TableCell>{config.name}</TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                    {config.start_url}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {config.schedule_cron}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={config.active ? 'Active' : 'Inactive'}
                    color={config.active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {format(new Date(config.created_at), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleRunJob(config.id)}
                    disabled={!config.active || runJobMutation.isLoading}
                  >
                    <RunIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleEdit(config)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => setDeleteConfirm(config)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingConfig ? 'Edit Configuration' : 'Create Configuration'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <Controller
              name="name"
              control={control}
              rules={{ required: 'Name is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Name"
                  margin="normal"
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              )}
            />
            
            <Controller
              name="start_url"
              control={control}
              rules={{ required: 'URL is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Start URL"
                  margin="normal"
                  error={!!errors.start_url}
                  helperText={errors.start_url?.message}
                />
              )}
            />
            
            <Controller
              name="css_selector"
              control={control}
              rules={{ required: 'CSS selector is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="CSS Selector"
                  margin="normal"
                  error={!!errors.css_selector}
                  helperText={errors.css_selector?.message}
                />
              )}
            />
            
            <Controller
              name="schedule_cron"
              control={control}
              rules={{ required: 'Schedule is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Cron Schedule"
                  margin="normal"
                  error={!!errors.schedule_cron}
                  helperText={errors.schedule_cron?.message || 'e.g., "0 * * * *" for hourly'}
                />
              )}
            />
            
            <Controller
              name="gemini_prompt"
              control={control}
              rules={{ required: 'Gemini prompt is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Gemini Prompt"
                  margin="normal"
                  multiline
                  rows={3}
                  error={!!errors.gemini_prompt}
                  helperText={errors.gemini_prompt?.message}
                />
              )}
            />
            
            <Controller
              name="active"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Switch {...field} checked={field.value} />}
                  label="Active"
                  sx={{ mt: 2 }}
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit(handleCreateEdit)}
            variant="contained"
            disabled={createMutation.isLoading || updateMutation.isLoading}
          >
            {editingConfig ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{deleteConfirm?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>Cancel</Button>
          <Button
            onClick={() => handleDelete(deleteConfirm.id)}
            color="error"
            variant="contained"
            disabled={deleteMutation.isLoading}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Configs;