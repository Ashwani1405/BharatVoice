import { Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Onboard from './pages/Onboard';
import KYC from './pages/KYC';
import Dashboard from './pages/Dashboard';
import KYCQueue from './pages/admin/KYCQueue';
import FraudMonitor from './pages/admin/FraudMonitor';

// Simple protected route wrapper
const ProtectedRoute = ({ children, adminOnly = false }: { children: React.ReactNode, adminOnly?: boolean }) => {
  // In a real app, this would use useAuth() logic
  const isAuthenticated = true; // Placeholder
  const isAdmin = true; // Placeholder

  if (!isAuthenticated) return <Navigate to="/" />;
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" />;

  return children;
};

function App() {
  return (
    <div className="min-h-screen bg-fintech-dark text-fintech-text flex flex-col font-sans">
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboard" element={<Onboard />} />
          <Route path="/kyc" element={<KYC />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/admin/kyc" element={
            <ProtectedRoute adminOnly>
              <KYCQueue />
            </ProtectedRoute>
          } />
          
          <Route path="/admin/fraud" element={
            <ProtectedRoute adminOnly>
              <FraudMonitor />
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  );
}

export default App;
