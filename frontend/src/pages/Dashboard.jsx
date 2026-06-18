import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function Dashboard() {
  const [plots, setPlots] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', crop_type: '', location: '', growth_stage: '', sowing_date: '' });

  useEffect(() => { fetchPlots(); }, []);

  const fetchPlots = async () => {
    const { data } = await api.get('/plots');
    setPlots(data);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    await api.post('/plots', formData);
    setShowForm(false);
    setFormData({ name: '', crop_type: '', location: '', growth_stage: '', sowing_date: '' });
    fetchPlots();
  };

  const handleDelete = async (id) => {
    if (confirm('Delete this plot?')) {
      await api.delete(`/plots/${id}`);
      fetchPlots();
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold">Your Plots</h2>
        <button onClick={() => setShowForm(!showForm)} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
          + Add Plot
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow-md mb-8 grid grid-cols-2 gap-4">
          <input placeholder="Plot Name" className="border p-2 rounded" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
          <input placeholder="Crop Type (e.g. Tomato)" className="border p-2 rounded" value={formData.crop_type} onChange={e => setFormData({...formData, crop_type: e.target.value})} required />
          <input placeholder="City Location (e.g. Pune)" className="border p-2 rounded" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} required />
          <input placeholder="Growth Stage (e.g. Flowering)" className="border p-2 rounded" value={formData.growth_stage} onChange={e => setFormData({...formData, growth_stage: e.target.value})} required />
          <input type="date" className="border p-2 rounded" value={formData.sowing_date} onChange={e => setFormData({...formData, sowing_date: e.target.value})} required />
          <button type="submit" className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700 col-span-2">Save Plot</button>
        </form>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plots.map(plot => (
          <div key={plot.id} className="bg-white rounded-lg shadow-md border overflow-hidden">
            <div className={`p-4 border-b ${plot.latest_risk?.severity === 'HIGH' ? 'bg-red-50' : plot.latest_risk?.severity === 'MODERATE' ? 'bg-yellow-50' : plot.latest_risk?.severity === 'LOW' ? 'bg-green-50' : 'bg-gray-50'}`}>
              <div className="flex justify-between items-start">
                <h3 className="text-xl font-bold">{plot.name}</h3>
                {plot.latest_risk && (
                  <span className={`px-2 py-1 text-xs font-bold rounded ${plot.latest_risk.severity === 'HIGH' ? 'bg-red-200 text-red-800' : plot.latest_risk.severity === 'MODERATE' ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'}`}>
                    {plot.latest_risk.severity} RISK
                  </span>
                )}
              </div>
              <p className="text-gray-600">{plot.crop_type} • {plot.location}</p>
            </div>
            <div className="p-4 text-sm space-y-2">
              <p><strong>Stage:</strong> {plot.growth_stage}</p>
              {plot.latest_risk ? (
                <>
                  <p><strong>Risk Score:</strong> {plot.latest_risk.risk_score}/100</p>
                  <p className="text-gray-700 italic truncate">"{plot.latest_risk.primary_risk}"</p>
                </>
              ) : (
                <p className="text-gray-500 italic">No risk assessment generated yet.</p>
              )}
            </div>
            <div className="p-4 bg-gray-50 border-t flex gap-2">
              <Link to={`/plots/${plot.id}`} className="flex-1 text-center bg-green-100 text-green-700 py-2 rounded hover:bg-green-200 font-medium">
                View Risk Report
              </Link>
              <button onClick={() => handleDelete(plot.id)} className="bg-red-100 text-red-700 px-3 py-2 rounded hover:bg-red-200">
                Delete
              </button>
            </div>
          </div>
        ))}
        {plots.length === 0 && !showForm && (
          <div className="col-span-full text-center py-12 text-gray-500">
            No plots registered. Add a plot to start tracking crop risks.
          </div>
        )}
      </div>
    </div>
  );
}
