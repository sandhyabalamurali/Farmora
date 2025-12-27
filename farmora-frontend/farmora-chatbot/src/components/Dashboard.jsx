import React, { useEffect, useState } from 'react';
import api from '../services/api';

const Dashboard = ({ user }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    Promise.all([api.getUserProfile(), api.getTimeline(user.user_id)])
      .then(([profile, timeline]) => {
        setData({ profile, timeline: timeline.timeline || [] });
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="p-6 text-gray-400">Loading dashboard...</div>;
  if (!data) return <div className="p-6 text-gray-400">No dashboard data.</div>;

  const weatherText = data.profile?.weather || 'Weather data unavailable';

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Dashboard</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-gray-800 rounded border border-gray-700">
          <div className="text-sm text-gray-400">Weather</div>
          <div className="mt-2 text-gray-200">{weatherText}</div>
        </div>

        <div className="p-4 bg-gray-800 rounded border border-gray-700">
          <div className="text-sm text-gray-400">Farm Summary</div>
          <div className="mt-2 text-gray-200">{data.profile ? `${data.profile.name || 'Farmer'}` : '—'}</div>
        </div>

        <div className="p-4 bg-gray-800 rounded border border-gray-700">
          <div className="text-sm text-gray-400">Upcoming Tasks</div>
          <div className="mt-2 text-gray-200">{(data.timeline || []).length} confirmed</div>
        </div>
      </div>

      <div>
        <div className="text-sm text-gray-400 mb-2">Market News</div>
        <div className="space-y-3">
          {(data.timeline || []).slice(0,3).map(item => (
            <div key={item.id} className="p-3 bg-gray-800 rounded border border-gray-700">
              <div className="flex justify-between items-center">
                <div className="text-sm font-semibold text-gray-100">{item.title}</div>
                <div className="text-xs text-gray-400">{item.date}</div>
              </div>
              {item.description && <div className="text-sm text-gray-300 mt-2">{item.description}</div>}
              {item.url && (
                <a href={item.url} target="_blank" rel="noreferrer" className="text-xs text-blue-400 mt-2 inline-block">Read more</a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
