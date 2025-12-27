import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  VerticalTimeline,
  VerticalTimelineElement
} from 'react-vertical-timeline-component';
import 'react-vertical-timeline-component/style.min.css';
import { Calendar, CheckCircle, Clock, Sprout, AlertCircle } from 'lucide-react';
import './Timeline.css';

const Timeline = ({ user }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await api.getTimeline(user.user_id);
      setItems(res.timeline || []);
    } catch (e) {
      console.error('Failed to load timeline', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [user]);

  const handleComplete = async (taskId) => {
    try {
      await api.completeTask(taskId, user.user_id);
      await load();
    } catch (e) {
      console.error('Complete failed', e);
      alert('Failed to mark task complete');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return { bg: '#dc2626', border: '#f87171' };
      case 'medium':
        return { bg: '#ca8a04', border: '#fbbf24' };
      case 'low':
        return { bg: '#16a34a', border: '#4ade80' };
      default:
        return { bg: '#16a34a', border: '#4ade80' };
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
            <Calendar className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text">
              Timeline
            </h2>
            <p className="text-sm text-gray-400">Your confirmed farming tasks and schedule</p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Clock className="w-8 h-8 text-green-500 animate-spin mx-auto mb-3" />
            <p className="text-gray-400">Loading your timeline...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && items.length === 0 && (
        <div className="text-center py-12 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <Sprout className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">No confirmed tasks yet</p>
          <p className="text-gray-500 text-sm">Start a conversation to get personalized farming tasks</p>
        </div>
      )}

      {/* Timeline */}
      {!loading && items.length > 0 && (
        <div data-testid="timeline-container">
          <VerticalTimeline lineColor="#166534">
            {items.map((item, index) => {
              const colors = getPriorityColor(item.priority);
              return (
                <VerticalTimelineElement
                  key={item.id || index}
                  date={item.date || 'No date'}
                  iconStyle={{ 
                    background: colors.bg, 
                    color: '#fff',
                    border: `3px solid ${colors.border}`,
                    boxShadow: `0 0 20px ${colors.border}40`
                  }}
                  icon={<Sprout />}
                  contentStyle={{
                    background: 'linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(17, 24, 39, 0.9) 100%)',
                    border: `1px solid ${colors.border}40`,
                    borderRadius: '12px',
                    boxShadow: `0 4px 20px rgba(0,0,0,0.3), 0 0 20px ${colors.border}20`
                  }}
                  contentArrowStyle={{ 
                    borderRight: `7px solid ${colors.border}40` 
                  }}
                  data-testid={`timeline-item-${index}`}
                >
                  {/* Priority Badge */}
                  <div className="mb-3">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${
                      item.priority === 'high' 
                        ? 'bg-red-500/20 text-red-300 border border-red-500/50' 
                        : item.priority === 'medium'
                        ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50'
                        : 'bg-green-500/20 text-green-300 border border-green-500/50'
                    }`}>
                      <AlertCircle className="w-3 h-3" />
                      {item.priority ? item.priority.toUpperCase() : 'NORMAL'} PRIORITY
                    </span>
                  </div>

                  {/* Task Title */}
                  <h4 className="text-xl font-bold text-green-100 mb-2 vertical-timeline-element-title">
                    {item.title}
                  </h4>

                  {/* Task Description */}
                  <p className="text-sm text-gray-300 leading-relaxed mb-4">
                    {item.description || 'No additional details provided.'}
                  </p>

                  {/* Action Button */}
                  <div className="flex items-center gap-3 mt-4">
                    <button
                      onClick={() => handleComplete(item.id)}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-lg text-sm text-white font-medium transition-all duration-200 shadow-lg hover:shadow-green-500/50"
                      data-testid={`complete-task-btn-${index}`}
                    >
                      <CheckCircle className="w-4 h-4" />
                      Mark Complete
                    </button>
                  </div>
                </VerticalTimelineElement>
              );
            })}
          </VerticalTimeline>
        </div>
      )}

      {/* Info Footer */}
      {!loading && items.length > 0 && (
        <div className="mt-8 p-4 bg-green-900/20 rounded-lg border border-green-800/30">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-green-300 mb-1">Task Management</h4>
              <p className="text-xs text-gray-400 leading-relaxed">
                Track your farming activities and mark them complete as you finish. 
                Completed tasks will help the AI provide better recommendations for your farm.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Timeline;
