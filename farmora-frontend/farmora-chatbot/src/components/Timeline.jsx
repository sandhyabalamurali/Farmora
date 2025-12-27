import React, { useEffect, useState, useCallback, useRef, useImperativeHandle, forwardRef } from 'react';
import api from '../services/api';
import { Calendar, CheckCircle, Clock, Sprout, AlertCircle } from 'lucide-react';
import { t } from '../i18n';

const Timeline = forwardRef(({ user, currentLanguage = 'en' }, ref) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState(null); // Track which task is being completed
  const loadingRef = useRef(false); // Prevent concurrent loads
  const lastLoadRef = useRef(0); // Debounce timestamp

  // Safe translation helper with fallback
  const translate = (key) => t(currentLanguage || 'en', key);

  const load = useCallback(async (force = false) => {
    if (!user) return;
    
    // Debounce: prevent loading more than once per second unless forced
    const now = Date.now();
    if (!force && (loadingRef.current || now - lastLoadRef.current < 1000)) {
      return;
    }
    
    loadingRef.current = true;
    lastLoadRef.current = now;
    setLoading(true);
    
    try {
      const res = await api.getTimeline(user.user_id);
      setItems(res.timeline || []);
    } catch (e) {
      console.error('Failed to load timeline', e);
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [user]);

  // Expose refresh method to parent components
  useImperativeHandle(ref, () => ({
    refresh: () => load(true)
  }));

  useEffect(() => {
    load(true); // Force load on mount or user change
  }, [user, load]);

  const handleComplete = async (taskId) => {
    if (completing) return; // Prevent double-clicks
    
    setCompleting(taskId);
    try {
      await api.completeTask(taskId, user.user_id);
      // Optimistically remove the completed task from UI
      setItems(prev => prev.filter(item => item.id !== taskId));
      // Then refresh to get server state
      await load(true);
    } catch (e) {
      console.error('Complete failed', e);
      alert(translate('complete_task_failed'));
      // Reload on error to restore state
      await load(true);
    } finally {
      setCompleting(null);
    }
  };

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'high':
        return {
          bg: 'bg-red-500',
          border: 'border-red-400',
          badge: 'bg-red-500/20 text-red-300 border-red-500/50',
          glow: 'shadow-red-500/30'
        };
      case 'medium':
        return {
          bg: 'bg-yellow-500',
          border: 'border-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
          glow: 'shadow-yellow-500/30'
        };
      case 'low':
      default:
        return {
          bg: 'bg-green-500',
          border: 'border-green-400',
          badge: 'bg-green-500/20 text-green-300 border-green-500/50',
          glow: 'shadow-green-500/30'
        };
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 relative">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-64 h-64 bg-green-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 left-20 w-80 h-80 bg-emerald-500/5 rounded-full blur-3xl"></div>
      </div>
      
      <div className="relative z-10">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-green-900/30">
            <Calendar className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text">
              {translate('timeline')}
            </h2>
            <p className="text-sm text-gray-400">{translate('confirmed_tasks')}</p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Clock className="w-8 h-8 text-green-400 animate-spin mx-auto mb-3" />
            <p className="text-gray-400">{translate('loading_timeline')}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && items.length === 0 && (
        <div className="text-center py-12 bg-gray-800/30 rounded-xl border border-green-700/30 backdrop-blur-sm">
          <Sprout className="w-16 h-16 text-green-600/50 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">{translate('no_confirmed_tasks')}</p>
          <p className="text-gray-500 text-sm">{translate('start_conversation')}</p>
        </div>
      )}

      {/* Custom Timeline */}
      {!loading && items.length > 0 && (
        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-green-500 via-emerald-600 to-green-700"></div>

          {/* Timeline Items */}
          <div className="space-y-6">
            {items.map((item, index) => {
              const styles = getPriorityStyles(item.priority);
              return (
                <div key={item.id || index} className="relative flex gap-6">
                  {/* Icon */}
                  <div className={`relative z-10 w-12 h-12 ${styles.bg} rounded-full flex items-center justify-center shadow-lg ${styles.glow} flex-shrink-0`}>
                    <Sprout className="w-6 h-6 text-white" />
                  </div>

                  {/* Content Card */}
                  <div className={`flex-1 bg-gray-800/40 backdrop-blur-sm rounded-xl p-5 border border-green-700/30 transition-all duration-300 hover:border-green-600/50 hover:bg-gray-800/60`}>
                    {/* Date */}
                    <div className="text-xs text-green-400 mb-2">{item.date || 'No date'}</div>

                    {/* Priority Badge */}
                    <div className="mb-3">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${styles.badge} border`}>
                        <AlertCircle className="w-3 h-3" />
                        {translate(item.priority || 'medium').toUpperCase()} {translate('priority').toUpperCase()}
                      </span>
                    </div>

                    {/* Task Title */}
                    <h4 className="text-xl font-bold text-green-100 mb-2">
                      {item.title}
                    </h4>

                    {/* Task Description */}
                    <p className="text-sm text-gray-300 leading-relaxed mb-4">
                      {item.description || translate('no_details')}
                    </p>

                    {/* Action Button */}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleComplete(item.id)}
                        disabled={completing === item.id}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white font-medium transition-all duration-200 shadow-lg ${
                          completing === item.id 
                            ? 'bg-gray-600 cursor-not-allowed' 
                            : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 shadow-green-900/30'
                        }`}
                      >
                        {completing === item.id ? (
                          <>
                            <Clock className="w-4 h-4 animate-spin" />
                            {translate('completing') || 'Completing...'}
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            {translate('mark_complete')}
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Info Footer */}
      {!loading && items.length > 0 && (
        <div className="mt-8 p-4 bg-green-900/20 rounded-lg border border-green-700/30">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-green-300 mb-1">{translate('task_management')}</h4>
              <p className="text-xs text-gray-400 leading-relaxed">
                {translate('task_management_desc')}
              </p>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
});

// Add display name for debugging
Timeline.displayName = 'Timeline';

export default Timeline;
