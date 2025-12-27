import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  VerticalTimeline,
  VerticalTimelineElement
} from 'react-vertical-timeline-component';
import 'react-vertical-timeline-component/style.min.css';
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

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Timeline</h3>

      {loading && <div className="text-sm text-gray-400">Loading...</div>}
      {!loading && items.length === 0 && (
        <div className="text-gray-400">No confirmed tasks yet.</div>
      )}

      <VerticalTimeline>
        {items.map(item => (
          <VerticalTimelineElement
            key={item.id}
            date={item.date || 'No date'}
            iconStyle={{ background: item.priority === 'high' ? '#e53e3e' : '#2d3748', color: '#fff' }}
          >
            <h4 className="vertical-timeline-element-title text-gray-100">{item.title}</h4>
            <p className="text-sm text-gray-300">{item.description}</p>
            <div className="mt-3">
              <button
                onClick={() => handleComplete(item.id)}
                className="px-3 py-1 bg-green-600 rounded text-sm text-white"
              >
                Mark Complete
              </button>
            </div>
          </VerticalTimelineElement>
        ))}
      </VerticalTimeline>
    </div>
  );
};

export default Timeline;
