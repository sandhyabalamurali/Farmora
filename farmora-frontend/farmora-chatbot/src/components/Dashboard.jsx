import React, { useEffect, useState } from 'react';
import { Cloud, TrendingUp, ListTodo, MapPin, Thermometer, Droplets } from 'lucide-react';
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

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }
  
  if (!data) {
    return (
      <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
        <div className="text-gray-400">No dashboard data.</div>
      </div>
    );
  }

  const weatherText = data.profile?.weather || 'Weather data unavailable';

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text">
              Dashboard
            </h2>
            <p className="text-sm text-gray-400">Overview of your farm</p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6" data-testid="dashboard-stats">
        {/* Weather Card */}
        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 rounded-xl p-5 border border-blue-700/30 hover:border-blue-600/50 transition-all duration-300 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <Cloud className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-sm font-semibold text-blue-300">Weather</div>
          </div>
          <div className="text-gray-200 text-sm leading-relaxed line-clamp-3">
            {weatherText}
          </div>
        </div>

        {/* Farm Summary Card */}
        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 rounded-xl p-5 border border-green-700/30 hover:border-green-600/50 transition-all duration-300 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
              <MapPin className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-sm font-semibold text-green-300">Farm Summary</div>
          </div>
          <div className="space-y-2">
            <div className="text-gray-200 font-medium">{data.profile?.name || 'Farmer'}</div>
            {user?.farm_location && (
              <div className="text-xs text-gray-400">{user.farm_location}</div>
            )}
            {user?.crops && user.crops.length > 0 && (
              <div className="text-xs text-gray-400">Growing: {user.crops.join(', ')}</div>
            )}
          </div>
        </div>

        {/* Tasks Card */}
        <div className="bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 rounded-xl p-5 border border-emerald-700/30 hover:border-emerald-600/50 transition-all duration-300 shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <ListTodo className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-sm font-semibold text-emerald-300">Tasks</div>
          </div>
          <div className="text-gray-200">
            <span className="text-3xl font-bold text-emerald-300">{(data.timeline || []).length}</span>
            <span className="text-sm text-gray-400 ml-2">confirmed tasks</span>
          </div>
        </div>
      </div>

      {/* Recent Tasks Section */}
      <div className="bg-gradient-to-br from-gray-800/60 to-gray-900/60 rounded-xl p-6 border border-green-800/30 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <ListTodo className="w-5 h-5 text-green-400" />
          <h3 className="text-lg font-semibold text-green-200">Recent Tasks</h3>
        </div>
        
        {data.timeline && data.timeline.length > 0 ? (
          <div className="space-y-3">
            {data.timeline.slice(0, 5).map((item, index) => (
              <div 
                key={item.id || index} 
                className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-green-700/50 transition-all duration-200"
                data-testid={`task-item-${index}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-sm font-semibold text-gray-100">{item.title}</div>
                  <div className="text-xs text-gray-400">{item.date}</div>
                </div>
                {item.description && (
                  <div className="text-sm text-gray-300 line-clamp-2">{item.description}</div>
                )}
                <div className="mt-2">
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                    item.priority === 'high' 
                      ? 'bg-red-500/20 text-red-300' 
                      : item.priority === 'medium'
                      ? 'bg-yellow-500/20 text-yellow-300'
                      : 'bg-green-500/20 text-green-300'
                  }`}>
                    {item.priority || 'normal'} priority
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No tasks yet. Start chatting to get personalized recommendations!
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="mt-6 p-4 bg-green-900/20 rounded-lg border border-green-800/30">
        <div className="flex items-start gap-3">
          <Thermometer className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-green-300 mb-1">Smart Dashboard</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              Your personalized farming dashboard shows weather insights, upcoming tasks, and quick access to important information. 
              Visit the Market tab for latest agricultural news and price updates.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
