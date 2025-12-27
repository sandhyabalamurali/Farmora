import React, { useEffect, useState, useCallback } from 'react';
import { TrendingUp, Newspaper, ExternalLink, RefreshCw, Cloud, Sparkles, Thermometer, Droplets, Wind, Eye, Sun, X, Calendar, Clock, ArrowUpRight, Leaf } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';
import { t } from '../i18n';

// Markdown components for professional text formatting
const MarkdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic text-blue-200">{children}</em>,
  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1 ml-2">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1 ml-2">{children}</ol>,
  li: ({ children }) => <li className="text-gray-200">{children}</li>,
  h1: ({ children }) => <h1 className="text-lg font-bold mb-2 text-blue-100">{children}</h1>,
  h2: ({ children }) => <h2 className="text-base font-bold mb-2 text-blue-100">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-bold mb-1 text-blue-200">{children}</h3>,
  code: ({ children }) => <code className="bg-black/30 px-1.5 py-0.5 rounded text-xs font-mono text-yellow-300">{children}</code>,
};

const Dashboard = ({ user, currentLanguage = 'en' }) => {
  const [marketData, setMarketData] = useState([]);
  const [weatherData, setWeatherData] = useState(null);
  const [rawWeatherText, setRawWeatherText] = useState('');
  const [newsLoading, setNewsLoading] = useState(false);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [newsLastUpdated, setNewsLastUpdated] = useState(null);
  const [weatherLastUpdated, setWeatherLastUpdated] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);

  // Cache keys for localStorage (per user)
  const getWeatherCacheKey = () => `farmora_weather_${user?.user_id}`;
  const getNewsCacheKey = () => `farmora_news_${user?.user_id}`;
  const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

  // Safe translation helper
  const translate = (key) => t(currentLanguage || 'en', key);

  // Check if cache is valid (within 24 hours)
  const isCacheValid = (lastUpdated) => {
    if (!lastUpdated) return false;
    const cacheTime = new Date(lastUpdated).getTime();
    const now = Date.now();
    return (now - cacheTime) < CACHE_DURATION;
  };

  // Load weather data
  const loadWeather = useCallback(async (forceRefresh = false) => {
    if (!user) return;
    
    // Check cache first
    if (!forceRefresh) {
      const cached = localStorage.getItem(getWeatherCacheKey());
      if (cached) {
        try {
          const { data, lastUpdated } = JSON.parse(cached);
          if (isCacheValid(lastUpdated)) {
            setRawWeatherText(data.weather || translate('weather_unavailable'));
            if (data.weather_structured) setWeatherData(data.weather_structured);
            setWeatherLastUpdated(lastUpdated);
            return;
          }
        } catch (e) {
          console.error('Cache parse error:', e);
        }
      }
    }

    setWeatherLoading(true);
    try {
      const response = await api.getWeatherData(user.user_id, currentLanguage);
      setRawWeatherText(response.weather || translate('weather_unavailable'));
      if (response.weather_structured) setWeatherData(response.weather_structured);
      const now = new Date().toISOString();
      setWeatherLastUpdated(now);
      
      // Cache the result
      localStorage.setItem(getWeatherCacheKey(), JSON.stringify({
        data: response,
        lastUpdated: now
      }));
    } catch (err) {
      console.error('Failed to load weather data', err);
    } finally {
      setWeatherLoading(false);
    }
  }, [user, currentLanguage]);

  // Load news data
  const loadNews = useCallback(async (forceRefresh = false) => {
    if (!user) return;
    
    // Check cache first (only if not forcing refresh)
    if (!forceRefresh) {
      const cached = localStorage.getItem(getNewsCacheKey());
      if (cached) {
        try {
          const { data, lastUpdated } = JSON.parse(cached);
          if (isCacheValid(lastUpdated)) {
            setMarketData(data || []);
            setNewsLastUpdated(lastUpdated);
            return;
          }
        } catch (e) {
          console.error('Cache parse error:', e);
        }
      }
    }

    setNewsLoading(true);
    try {
      // Pass refresh=true to fetch fresh data from API
      const response = await api.getNewsData(user.user_id, currentLanguage, forceRefresh);
      setMarketData(response.market_data || []);
      const now = new Date().toISOString();
      setNewsLastUpdated(now);
      
      // Cache the result
      localStorage.setItem(getNewsCacheKey(), JSON.stringify({
        data: response.market_data || [],
        lastUpdated: now
      }));
    } catch (err) {
      console.error('Failed to load news data', err);
    } finally {
      setNewsLoading(false);
    }
  }, [user, currentLanguage]);

  // Initial load - use cache if available
  useEffect(() => {
    loadWeather(false);
    loadNews(false);
  }, [user, loadWeather, loadNews]);

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recently';
    }
  };

  // Article Modal Component - Clean Professional Design
  const ArticleModal = ({ article, onClose }) => {
    if (!article) return null;
    
    // Extract clean URL
    const articleUrl = article.url || article.href || article.link || '';
    
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
        <div 
          className="bg-gray-900 rounded-2xl max-w-xl w-full max-h-[85vh] overflow-hidden shadow-2xl border border-green-700/30"
          onClick={e => e.stopPropagation()}
        >
          {/* Article Image */}
          {article.image_url && (
            <div className="relative h-48 overflow-hidden">
              <img 
                src={article.image_url} 
                alt={article.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.parentElement.style.display = 'none';
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
            </div>
          )}
          
          {/* Close Button */}
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/70 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>

          {/* Content */}
          <div className="p-6">
            {/* Meta Info */}
            <div className="flex items-center gap-3 mb-4 flex-wrap">
              {article.source && (
                <span className="px-2.5 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-md">
                  {article.source}
                </span>
              )}
              <div className="flex items-center gap-1.5 text-gray-400 text-xs">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatDate(article.published_at)}</span>
              </div>
            </div>

            {/* Title */}
            <h2 className="text-lg font-semibold text-white mb-4 leading-snug">
              {article.title}
            </h2>

            {/* Summary */}
            <p className="text-gray-300 text-sm leading-relaxed mb-6">
              {article.summary || article.description || 'No summary available.'}
            </p>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-green-700/20">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm"
              >
                Close
              </button>
              {articleUrl && (
                <a
                  href={articleUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-lg font-medium transition-all text-sm shadow-lg shadow-green-900/30"
                >
                  <span>Read Full Article</span>
                  <ArrowUpRight className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 relative">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-green-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-40 right-20 w-80 h-80 bg-emerald-500/5 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/3 rounded-full blur-3xl"></div>
      </div>
      
      <div className="relative z-10">
      {/* Professional Header - Minimal & Clean */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full"></div>
              <div className="relative w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-900/30">
                <Leaf className="w-6 h-6 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text">
                {translate('farm_dashboard') || 'Farm Dashboard'}
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">{translate('latest_insights') || 'Real-time agricultural insights'}</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-green-500/10 rounded-lg border border-green-500/30">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400 font-medium">Live</span>
          </div>
        </div>
      </div>

      {/* Weather Card - Premium Design */}
      <div className="mb-8 bg-gray-800/40 backdrop-blur-sm rounded-2xl overflow-hidden border border-green-700/30 shadow-xl">
        {/* Weather Header */}
        <div className="bg-gradient-to-r from-gray-800/60 to-gray-800/40 px-5 py-4 flex items-center justify-between border-b border-green-700/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center border border-blue-400/30">
              <Cloud className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{translate('weather_insights') || 'Weather Insights'}</h3>
              <p className="text-xs text-gray-400">
                {weatherLastUpdated 
                  ? `${translate('updated') || 'Updated'} ${new Date(weatherLastUpdated).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`
                  : translate('ai_powered_forecast') || 'AI-Powered Forecast'}
              </p>
            </div>
          </div>
          <button
            onClick={() => loadWeather(true)}
            disabled={weatherLoading}
            className="p-2.5 bg-gray-700/50 hover:bg-green-900/40 text-gray-300 rounded-lg transition-all duration-200 border border-green-700/30 hover:border-green-600/50 disabled:opacity-50"
            title={translate('refresh_weather') || 'Refresh Weather'}
          >
            <RefreshCw className={`w-4 h-4 ${weatherLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Weather Content */}
        <div className="p-5">
          {weatherLoading ? (
            <div className="flex flex-col items-center justify-center py-10">
              <div className="w-12 h-12 border-3 border-gray-600 border-t-green-400 rounded-full animate-spin mb-3"></div>
              <span className="text-gray-400 text-sm">{translate('loading_weather') || 'Loading weather data...'}</span>
            </div>
          ) : (
            <>
              {/* AI Insights Card */}
              <div className="bg-gradient-to-r from-gray-800/40 via-blue-900/20 to-gray-800/40 rounded-2xl p-5 border border-blue-500/20 mb-5">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center flex-shrink-0 border border-blue-400/30">
                    <Sparkles className="w-5 h-5 text-blue-300" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-blue-200 mb-3 uppercase tracking-wide">AI Weather Analysis</h4>
                    <div className="text-gray-200 text-sm leading-relaxed">
                      <ReactMarkdown components={MarkdownComponents}>
                        {rawWeatherText}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats Row - Minimal Design */}
              {weatherData && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {weatherData.temperature && (
                    <div className="bg-gray-800/40 rounded-xl p-4 text-center border border-green-700/20 hover:border-green-600/40 transition-colors">
                      <Thermometer className="w-5 h-5 text-orange-400 mx-auto mb-2" />
                      <p className="text-xl font-semibold text-white">{weatherData.temperature}°C</p>
                      <p className="text-xs text-gray-400 mt-1">{translate('temperature') || 'Temperature'}</p>
                    </div>
                  )}
                  {weatherData.humidity && (
                    <div className="bg-gray-800/40 rounded-xl p-4 text-center border border-green-700/20 hover:border-green-600/40 transition-colors">
                      <Droplets className="w-5 h-5 text-cyan-400 mx-auto mb-2" />
                      <p className="text-xl font-semibold text-white">{weatherData.humidity}%</p>
                      <p className="text-xs text-gray-400 mt-1">{translate('humidity') || 'Humidity'}</p>
                    </div>
                  )}
                  {weatherData.wind_speed && (
                    <div className="bg-gray-800/40 rounded-xl p-4 text-center border border-green-700/20 hover:border-green-600/40 transition-colors">
                      <Wind className="w-5 h-5 text-teal-400 mx-auto mb-2" />
                      <p className="text-xl font-semibold text-white">{weatherData.wind_speed}</p>
                      <p className="text-xs text-gray-400 mt-1">{translate('wind') || 'Wind'}</p>
                    </div>
                  )}
                  {weatherData.visibility && (
                    <div className="bg-gray-800/40 rounded-xl p-4 text-center border border-green-700/20 hover:border-green-600/40 transition-colors">
                      <Eye className="w-5 h-5 text-purple-400 mx-auto mb-2" />
                      <p className="text-xl font-semibold text-white">{weatherData.visibility}</p>
                      <p className="text-xs text-gray-400 mt-1">{translate('visibility') || 'Visibility'}</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Market News Section - Premium Design */}
      <div className="mb-8">
        {/* News Header with Refresh */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/20 rounded-xl flex items-center justify-center border border-green-500/30">
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{translate('market_updates') || 'Agricultural News'}</h3>
              {newsLastUpdated && (
                <p className="text-xs text-gray-400">
                  {translate('updated') || 'Updated'} {new Date(newsLastUpdated).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={() => loadNews(true)}
            disabled={newsLoading}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800/50 hover:bg-green-900/40 text-gray-300 rounded-lg transition-colors border border-green-700/30 hover:border-green-600/50"
            data-testid="refresh-news-btn"
          >
            <RefreshCw className={`w-4 h-4 ${newsLoading ? 'animate-spin' : ''}`} />
            <span className="text-sm">{translate('refresh') || 'Refresh'}</span>
          </button>
        </div>

        {/* Loading State */}
        {newsLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 border-3 border-gray-600 border-t-green-400 rounded-full animate-spin mb-3"></div>
            <p className="text-gray-400 text-sm">{translate('loading_news') || 'Loading news...'}</p>
          </div>
        )}

        {/* Empty State */}
        {!newsLoading && marketData.length === 0 && (
          <div className="text-center py-12 bg-gray-800/30 rounded-xl border border-green-700/30">
            <Newspaper className="w-10 h-10 text-green-600/50 mx-auto mb-3" />
            <p className="text-gray-300 font-medium mb-1">{translate('no_news') || 'No news available'}</p>
            <p className="text-gray-500 text-sm">{translate('check_back_later') || 'Check back later for updates'}</p>
          </div>
        )}

        {/* News Grid - Premium Clean Cards */}
        {!newsLoading && marketData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="market-news-grid">
            {marketData.filter(item => item.url && item.url !== 'undefined' && item.url !== 'null').map((item, index) => (
              <div
                key={item.id || index}
                className="bg-gray-800/40 backdrop-blur-sm rounded-xl overflow-hidden border border-green-700/30 hover:border-green-600/50 transition-all duration-300 cursor-pointer group"
                data-testid={`market-news-item-${index}`}
                onClick={() => setSelectedArticle(item)}
              >
                {/* Article Image */}
                {item.image_url && (
                  <div className="relative h-40 overflow-hidden">
                    <img 
                      src={item.image_url} 
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        e.target.parentElement.style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent" />
                    {item.source && (
                      <span className="absolute top-3 left-3 px-2 py-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-xs font-medium rounded-md shadow-lg">
                        {item.source}
                      </span>
                    )}
                  </div>
                )}

                <div className="p-4">
                  {/* Header - only show if no image */}
                  {!item.image_url && item.source && (
                    <div className="flex items-center gap-2 mb-3">
                      <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-md">
                        {item.source}
                      </span>
                      <span className="text-xs text-gray-500">{formatDate(item.published_at)}</span>
                    </div>
                  )}

                  {/* Date if image exists */}
                  {item.image_url && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
                      <Calendar className="w-3 h-3" />
                      <span>{formatDate(item.published_at)}</span>
                    </div>
                  )}

                  {/* Title */}
                  <h3 className="text-sm font-semibold text-white mb-2 line-clamp-2 group-hover:text-green-400 transition-colors leading-snug">
                    {item.title}
                  </h3>

                  {/* Summary */}
                  {(item.summary || item.description) && (
                    <p className="text-xs text-gray-400 mb-3 line-clamp-2 leading-relaxed">
                      {item.summary || item.description}
                    </p>
                  )}

                  {/* Read More */}
                  <div className="flex items-center justify-between pt-3 border-t border-green-700/20">
                    <span className="text-xs text-gray-500">{translate('click_to_read') || 'Read more'}</span>
                    <ArrowUpRight className="w-4 h-4 text-gray-500 group-hover:text-green-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Article Modal */}
      {selectedArticle && (
        <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
      )}

      {/* Footer Info - Premium Design */}
      <div className="mt-6 p-4 bg-green-900/20 rounded-xl border border-green-700/30">
        <div className="flex items-center gap-3">
          <Sparkles className="w-4 h-4 text-green-400 flex-shrink-0" />
          <p className="text-xs text-gray-400">
            {translate('ai_curated_desc') || 'AI-curated agricultural news and insights, updated regularly.'}
          </p>
        </div>
      </div>
      </div>
    </div>
  );
};

export default Dashboard;
