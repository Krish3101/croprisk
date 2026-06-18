import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

export default function PlotDetail() {
  const { id } = useParams();
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const { data } = await api.get(`/plots/${id}/risk`);
        setRisk(data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to fetch risk assessment');
      } finally {
        setLoading(false);
      }
    };
    fetchRisk();
  }, [id]);

  if (loading) return <div className="text-center py-20 text-gray-600">Generating AI Risk Analysis (Checking Weather & Agronomic Rules)...</div>;
  if (error) return <div className="text-center py-20 text-red-600 bg-red-50 rounded-lg">{error}</div>;
  if (!risk) return null;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-green-600 hover:underline">&larr; Back to Dashboard</Link>
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden border">
        <div className={`p-6 border-b ${risk.severity === 'HIGH' ? 'bg-red-600 text-white' : risk.severity === 'MODERATE' ? 'bg-yellow-500 text-white' : 'bg-green-600 text-white'}`}>
          <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold">Risk Assessment</h2>
            <div className="text-right">
              <span className="text-5xl font-black">{risk.risk_score}</span><span className="text-xl opacity-80">/100</span>
              <p className="font-bold uppercase tracking-wider">{risk.severity} RISK</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm uppercase tracking-wide text-gray-500 font-bold mb-1">Primary Threat</h3>
            <p className="text-xl font-semibold text-gray-900">{risk.primary_risk}</p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-sm uppercase tracking-wide text-gray-500 font-bold mb-2">Weather Context</h3>
            <p className="text-gray-800 leading-relaxed italic">{risk.weather_summary}</p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="text-sm uppercase tracking-wide text-gray-500 font-bold mb-2">AI Agronomic Analysis</h3>
            <p className="text-gray-800 leading-relaxed">{risk.analysis}</p>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <h3 className="text-sm uppercase tracking-wide text-blue-800 font-bold mb-2">Recommended Action</h3>
            <p className="text-blue-900 font-medium text-lg leading-relaxed">{risk.recommendation}</p>
          </div>
          
          <div className="text-xs text-gray-400 text-right mt-4">
            Report Generated: {new Date(risk.created_at).toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
