import React, { useEffect, useState } from 'react';
import { TrendingUp, Newspaper, ExternalLink, RefreshCw, Cloud, Sparkles } from 'lucide-react';
import api from '../services/api';

const Dashboard = ({ user }) => {
  const [marketData, setMarketData] = useState([]);
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const [profile, market] = await Promise.all([
        api.getUserProfile(),
        api.getMarketData(user.user_id)
      ]);
      setProfileData(profile);
      setMarketData(market.market_data || []);
      setLastUpdated(market.last_updated);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recently';
    }
  };

  const weatherText = profileData?.weather || 'Weather data unavailable';

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text">
                AI-Powered Personalised News
              </h2>
              <p className="text-sm text-gray-400">Latest agricultural insights curated for you</p>
            </div>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 bg-green-900/40 hover:bg-green-800/60 text-green-400 rounded-lg transition-all duration-200 border border-green-700/30"
            data-testid="refresh-dashboard-btn"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {lastUpdated && (
          <p className="text-xs text-gray-500 ml-16">
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </p>
        )}
      </div>

      {/* Weather Card */}
      <div className="mb-6 bg-gradient-to-br from-blue-900/40 to-blue-800/20 rounded-xl p-5 border border-blue-700/30 hover:border-blue-600/50 transition-all duration-300 shadow-lg">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <Cloud className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-sm font-semibold text-blue-300">Weather Insights</div>
        </div>
        <div className="text-gray-200 text-sm leading-relaxed">
          {weatherText}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-green-500 animate-spin mx-auto mb-3" />
            <p className="text-gray-400">Loading latest news...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && marketData.length === 0 && (
        <div className="text-center py-12 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <Newspaper className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">No news available</p>
          <p className="text-gray-500 text-sm">Check back later for AI-curated agricultural updates</p>
        </div>
      )}

      {/* Market News Grid */}
      {!loading && marketData.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-green-200">Agricultural News & Market Insights</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="market-news-grid">
            {marketData.map((item, index) => (
              <div
                key={item.id || index}
                className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-xl p-5 border border-green-900/30 hover:border-green-700/50 transition-all duration-300 shadow-lg hover:shadow-green-900/20 backdrop-blur-sm"
                data-testid={`market-news-item-${index}`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-green-900/40 rounded-lg flex items-center justify-center">
                      <Newspaper className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="flex flex-col">
                      {item.source && (
                        <span className="text-xs text-green-400 font-medium">{item.source}</span>
                      )}
                      <span className="text-xs text-gray-500">{formatDate(item.published_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold text-gray-100 mb-2 line-clamp-2">
                  {item.title}
                </h3>

                {/* Summary or Description */}
                {item.summary && (
                  <p className="text-sm text-gray-300 mb-3 line-clamp-3">
                    {item.summary}
                  </p>
                )}
                {!item.summary && item.description && (
                  <p className="text-sm text-gray-400 mb-3 line-clamp-3">
                    {item.description}
                  </p>
                )}

                {/* Read More Link */}
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-green-400 hover:text-green-300 transition-colors group"
                    data-testid={`read-more-link-${index}`}
                  >
                    <span>Read full article</span>
                    <ExternalLink className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-8 p-4 bg-green-900/20 rounded-lg border border-green-800/30">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-green-300 mb-1">AI-Curated Intelligence</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              Our AI analyzes thousands of agricultural news sources and selects the most relevant updates for Indian farmers. 
              News is refreshed every 30 minutes with the latest market trends, weather insights, and farming tips.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
