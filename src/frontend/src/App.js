import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Configs from './pages/Configs';
import Results from './pages/Results';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Navbar />
                  <Box component="main" sx={{ p: 3, mt: 8 }}>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/configs" element={<Configs />} />
                      <Route path="/results" element={<Results />} />
                    </Routes>
                  </Box>
                </ProtectedRoute>
              }
            />
          </Routes>
        </Box>
      </Router>
    </AuthProvider>
  );
}

export default App;