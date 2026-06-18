import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PlotDetail from './pages/PlotDetail';

const PrivateRoute = ({ children }) => {
  return localStorage.getItem('token') ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <header className="bg-green-700 text-white shadow-md p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">KisanAI Risk Intelligence V2</h1>
            {localStorage.getItem('token') && (
              <button 
                onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }}
                className="text-sm bg-green-800 px-3 py-1 rounded hover:bg-green-900"
              >
                Logout
              </button>
            )}
          </div>
        </header>
        <main className="container mx-auto p-4 py-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/plots/:id" element={<PrivateRoute><PlotDetail /></PrivateRoute>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
