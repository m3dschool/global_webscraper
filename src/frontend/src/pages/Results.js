import React, { useState } from 'react';
import {
  Container,
  Typography,
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
  Button,
  Box,
  Alert,
  CircularProgress,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import JSONPretty from 'react-json-pretty';
import { resultsApi } from '../services/api';
import { format } from 'date-fns';

const Results = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [viewResult, setViewResult] = useState(null);
  const [viewRawHtml, setViewRawHtml] = useState(null);
  
  const pageSize = 20;

  const { data: resultsData, isLoading, error } = useQuery(
    ['results', page, statusFilter],
    () => resultsApi.getAll(page, pageSize, null, statusFilter || null).then(res => res.data),
    { keepPreviousData: true }
  );

  const { data: rawHtmlData, isLoading: rawHtmlLoading } = useQuery(
    ['raw-html', viewRawHtml?.id],
    () => resultsApi.getRawHtml(viewRawHtml.id).then(res => res.data),
    { enabled: !!viewRawHtml }
  );

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'timeout':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (isLoading && !resultsData) {
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
          Failed to load results. Please try again.
        </Alert>
      </Container>
    );
  }

  const totalPages = Math.ceil((resultsData?.total || 0) / pageSize);

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Scrape Results
        </Typography>
        
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Status Filter</InputLabel>
          <Select
            value={statusFilter}
            label="Status Filter"
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="success">Success</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="timeout">Timeout</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Config ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Gemini Cost</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {resultsData?.results?.map((result) => (
              <TableRow key={result.id}>
                <TableCell>{result.config_id}</TableCell>
                <TableCell>
                  <Chip
                    label={result.status}
                    color={getStatusColor(result.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {format(new Date(result.started_at), 'MMM dd, HH:mm:ss')}
                </TableCell>
                <TableCell>
                  {result.duration_seconds ? `${result.duration_seconds.toFixed(1)}s` : '-'}
                </TableCell>
                <TableCell>
                  {result.gemini_cost ? `$${result.gemini_cost.toFixed(4)}` : '-'}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => setViewResult(result)}
                    title="View Details"
                  >
                    <ViewIcon />
                  </IconButton>
                  {result.status === 'success' && (
                    <IconButton
                      size="small"
                      onClick={() => setViewRawHtml(result)}
                      title="View Raw HTML"
                    >
                      <CodeIcon />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={3}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}

      {/* Result Details Dialog */}
      <Dialog 
        open={!!viewResult} 
        onClose={() => setViewResult(null)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          Result Details - ID: {viewResult?.id}
        </DialogTitle>
        <DialogContent>
          {viewResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Extracted Data
              </Typography>
              {viewResult.extracted_data ? (
                <Box sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      backgroundColor: '#1e1e1e',
                      borderRadius: '4px',
                      padding: '16px',
                      overflow: 'auto',
                      maxHeight: '400px'
                    }}
                  >
                    <JSONPretty 
                      data={viewResult.extracted_data}
                      theme={{
                        main: 'line-height:1.3;color:#d4d4d4;background:#1e1e1e;overflow:auto;',
                        error: 'line-height:1.3;color:#66d9ef;background:#1e1e1e;overflow:auto;',
                        key: 'color:#a6e22e;',
                        string: 'color:#e6db74;',
                        value: 'color:#ae81ff;',
                        boolean: 'color:#ae81ff;'
                      }}
                    />
                  </Box>
                </Box>
              ) : (
                <Typography color="textSecondary" gutterBottom>
                  No extracted data
                </Typography>
              )}

              {viewResult.gemini_response && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Gemini Response
                  </Typography>
                  <Box sx={{ mb: 3 }}>
                    <Box
                      sx={{
                        backgroundColor: '#1e1e1e',
                        borderRadius: '4px',
                        padding: '16px',
                        overflow: 'auto',
                        maxHeight: '400px'
                      }}
                    >
                      <JSONPretty 
                        data={viewResult.gemini_response}
                        theme={{
                          main: 'line-height:1.3;color:#d4d4d4;background:#1e1e1e;overflow:auto;',
                          error: 'line-height:1.3;color:#66d9ef;background:#1e1e1e;overflow:auto;',
                          key: 'color:#a6e22e;',
                          string: 'color:#e6db74;',
                          value: 'color:#ae81ff;',
                          boolean: 'color:#ae81ff;'
                        }}
                      />
                    </Box>
                  </Box>
                </>
              )}

              {viewResult.error_message && (
                <>
                  <Typography variant="h6" gutterBottom color="error">
                    Error Message
                  </Typography>
                  <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                    {viewResult.error_message}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewResult(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Raw HTML Dialog */}
      <Dialog 
        open={!!viewRawHtml} 
        onClose={() => setViewRawHtml(null)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          Raw HTML - Result ID: {viewRawHtml?.id}
        </DialogTitle>
        <DialogContent>
          {rawHtmlLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                URL: {rawHtmlData?.url}
              </Typography>
              <Box
                component="pre"
                sx={{
                  backgroundColor: '#1e1e1e',
                  color: '#d4d4d4',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: '400px',
                  fontSize: '0.875rem',
                  fontFamily: 'monospace',
                }}
              >
                {rawHtmlData?.raw_html || 'No raw HTML data'}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewRawHtml(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Results;