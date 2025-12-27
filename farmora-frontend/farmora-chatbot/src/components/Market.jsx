import React, { useEffect, useState } from 'react';
import { TrendingUp, Newspaper, ExternalLink, RefreshCw, DollarSign, Package } from 'lucide-react';
import api from '../services/api';

const Market = ({ user }) => {
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadMarketData = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await api.getMarketData(user.user_id);
      setMarketData(res.market_data || []);
      setLastUpdated(res.last_updated);
    } catch (e) {
      console.error('Failed to load market data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMarketData();
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

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text">
                Market Insights
              </h2>
              <p className="text-sm text-gray-400">Latest agricultural news and market trends</p>
            </div>
          </div>
          <button
            onClick={loadMarketData}
            disabled={loading}
            className="p-2 bg-green-900/40 hover:bg-green-800/60 text-green-400 rounded-lg transition-all duration-200 border border-green-700/30"
            data-testid="refresh-market-data-btn"
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

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-green-500 animate-spin mx-auto mb-3" />
            <p className="text-gray-400">Loading fresh market data...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && marketData.length === 0 && (
        <div className="text-center py-12 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <Package className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">No market data available</p>
          <p className="text-gray-500 text-sm">Check back later for updates</p>
        </div>
      )}

      {/* Market News Grid */}
      {!loading && marketData.length > 0 && (
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
      )}

      {/* Footer Info */}
      <div className="mt-8 p-4 bg-green-900/20 rounded-lg border border-green-800/30">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-green-300 mb-1">Market Intelligence</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              Stay informed with AI-curated agricultural news, market trends, and price updates 
              to make better farming decisions. Data is refreshed every 30 minutes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Market;
