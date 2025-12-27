import React, { useRef, useEffect, useState } from 'react';
import { MessageSquare, AlertCircle, CheckCircle, Leaf, Droplet, Bug, Thermometer, Wind, X, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { t } from '../i18n';
import './ChatWindow.css';

// Custom markdown components for better styling
const MarkdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-green-400">{children}</strong>,
  em: ({ children }) => <em className="italic text-gray-300">{children}</em>,
  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="ml-2">{children}</li>,
  h1: ({ children }) => <h1 className="text-xl font-bold mb-2 text-green-400">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-green-400">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-bold mb-1 text-green-400">{children}</h3>,
  h4: ({ children }) => <h4 className="text-sm font-bold mb-1 text-green-500">{children}</h4>,
  h5: ({ children }) => <h5 className="text-sm font-semibold mb-1">{children}</h5>,
  code: ({ children }) => <code className="bg-black/30 px-1.5 py-0.5 rounded text-sm font-mono text-yellow-300">{children}</code>,
  blockquote: ({ children }) => <blockquote className="border-l-3 border-green-500 pl-3 my-2 italic bg-green-900/20 py-2 rounded-r">{children}</blockquote>,
  hr: () => <hr className="my-3 border-green-700/30" />,
};

const ChatWindow = ({ messages, pendingTasks, onTaskConfirmation, currentLanguage = 'en', loading = false }) => {
  const messagesEndRef = useRef(null);
  const [taskStates, setTaskStates] = useState({}); // Track task states: { taskId: 'confirming' | 'accepted' | 'rejected' }
  const skipScrollRef = useRef(false);

  const scrollToBottom = () => {
    if (!skipScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    skipScrollRef.current = false;
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const DiseaseCard = ({ disease }) => {
    if (!disease) return null;
    
    return (
      <div className="disease-card">
        <div className="disease-header">
          <h4 className="disease-name">
            🌾 {disease.label}
            <span className="confidence-badge">{disease.confidence.toFixed(0)}% {t(currentLanguage, 'confidence')}</span>
          </h4>
          <div className={`severity-tag severity-${disease.severity}`}>
            {disease.severity.toUpperCase()}
          </div>
        </div>

        <div className="disease-content">
          <div className="disease-section">
            <h5>💊 {t(currentLanguage, 'remedy')}</h5>
            <p>{disease.remedy}</p>
          </div>

          <div className="disease-tips">
            <h5>🛡️ {t(currentLanguage, 'prevention')}</h5>
            <ul>
              {disease.prevention_tips?.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>

          {disease.immediate_action && (
            <div className="disease-action">
              <AlertCircle className="w-4 h-4" />
              <span><strong>{t(currentLanguage, 'immediate_action')}:</strong> {disease.immediate_action}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const PlannerCard = ({ task, onConfirmation }) => {
    if (!task) return null;
    
    const taskId = task.task_id || `task-${task.task_name}-${task.date}`;
    const taskState = taskStates[taskId];
    const isProcessing = taskState === 'confirming';
    const isAccepted = taskState === 'accepted';
    const isRejected = taskState === 'rejected';

    const handleAccept = async () => {
      skipScrollRef.current = true; // Prevent scroll on task confirmation
      setTaskStates(prev => ({ ...prev, [taskId]: 'confirming' }));
      try {
        await onConfirmation(task, true);
        setTaskStates(prev => ({ ...prev, [taskId]: 'accepted' }));
      } catch (error) {
        setTaskStates(prev => {
          const newState = { ...prev };
          delete newState[taskId];
          return newState;
        });
      }
    };

    const handleReject = async () => {
      skipScrollRef.current = true;
      setTaskStates(prev => ({ ...prev, [taskId]: 'confirming' }));
      try {
        await onConfirmation(task, false);
        setTaskStates(prev => ({ ...prev, [taskId]: 'rejected' }));
      } catch (error) {
        setTaskStates(prev => {
          const newState = { ...prev };
          delete newState[taskId];
          return newState;
        });
      }
    };

    // Determine card styling based on state
    const getCardClass = () => {
      let baseClass = 'planner-card';
      if (isAccepted) return `${baseClass} planner-card-accepted`;
      if (isRejected) return `${baseClass} planner-card-rejected`;
      if (isProcessing) return `${baseClass} planner-card-processing`;
      return baseClass;
    };

    return (
      <div className={getCardClass()}>
        {/* Status Overlay for accepted/rejected */}
        {(isAccepted || isRejected) && (
          <div className={`task-status-overlay ${isAccepted ? 'status-accepted' : 'status-rejected'}`}>
            <div className="status-icon-wrapper">
              {isAccepted ? (
                <CheckCircle className="status-icon" />
              ) : (
                <X className="status-icon" />
              )}
            </div>
            <span className="status-text">
              {isAccepted ? '✅ Added to Timeline!' : '❌ Declined'}
            </span>
          </div>
        )}

        <div className={`planner-card-content ${(isAccepted || isRejected) ? 'content-faded' : ''}`}>
          <div className="planner-header">
            <h4>📅 {task.task_name}</h4>
            <span className={`priority-tag priority-${task.priority}`}>
              {t(currentLanguage, task.priority) || task.priority.toUpperCase()}
            </span>
          </div>

          <div className="planner-content">
            <p className="task-date">📆 {task.date}</p>
            <p className="task-reason">💡 {task.reason}</p>
            
            {task.description && (
              <p className="task-description">{task.description}</p>
            )}

            {task.estimated_hours && (
              <p className="task-time">⏱️ {t(currentLanguage, 'estimated')}: {task.estimated_hours} {t(currentLanguage, 'hours')}</p>
            )}

            {task.safety_notes && (
              <div className="safety-notes">
                ⚠️ <strong>{t(currentLanguage, 'safety')}:</strong> {task.safety_notes}
              </div>
            )}

            {task.requires_confirmation && !isAccepted && !isRejected && (
              <div className="task-actions">
                <button
                  onClick={handleAccept}
                  disabled={isProcessing}
                  className={`btn-confirm ${isProcessing ? 'btn-processing' : ''}`}
                >
                  {isProcessing ? (
                    <>
                      <Clock className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>✓ {t(currentLanguage, 'accept_task')}</>
                  )}
                </button>
                <button
                  onClick={handleReject}
                  disabled={isProcessing}
                  className="btn-reject"
                >
                  ✕ {t(currentLanguage, 'decline_task')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const DashboardCard = ({ data }) => {
    if (!data) return null;

    return (
      <div className="dashboard-card">
        <h4>📊 {t(currentLanguage, 'farm_dashboard')}</h4>

        {data.weather && (
          <div className="weather-section">
            <h5>🌤️ {t(currentLanguage, 'weather_forecast')}</h5>
            <p>{data.weather}</p>
          </div>
        )}

        {data.market_news && data.market_news.length > 0 && (
          <div className="news-section">
            <h5>📰 {t(currentLanguage, 'market_updates')}</h5>
            <div className="news-list">
              {data.market_news.slice(0, 3).map((news, idx) => (
                <div key={idx} className="news-item">
                  <h6>{news.title}</h6>
                  <p>{news.description}</p>
                  <small>🔗 {news.source}</small>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-transparent overflow-y-auto">
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message-container ${message.sender}`}>
            <div className="message-content">
              {message.sender === 'agent' && (
                <div className="agent-header">
                  <div className="agent-avatar">🤖</div>
                  <span>FarMora Assistant</span>
                </div>
              )}

              {message.image && (
                <div className="message-image">
                  <img src={message.image} alt="Uploaded" />
                  <p className="image-caption">{message.text}</p>
                </div>
              )}

              {!message.image && (
                <div className={`message-bubble ${message.sender}`}>
                  {message.sender === 'agent' ? (
                    <ReactMarkdown components={MarkdownComponents}>
                      {message.text}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.text}</p>
                  )}
                </div>
              )}

              {/* Rich Data Rendering */}
              {message.data && (
                <div className="message-data">
                  {message.data.diseaseResult && (
                    <DiseaseCard disease={message.data.diseaseResult} />
                  )}

                  {message.data.plannerSuggestions && message.data.plannerSuggestions.length > 0 && (
                    <div className="planner-section">
                      <h4>📋 {t(currentLanguage, 'suggested_tasks')}</h4>
                      {message.data.plannerSuggestions.map((task, idx) => (
                        <PlannerCard
                          key={task.task_id || `task-${task.task_name}-${task.date}-${idx}`}
                          task={task}
                          onConfirmation={onTaskConfirmation}
                        />
                      ))}
                    </div>
                  )}

                  {message.data.dashboardData && (
                    <DashboardCard data={message.data.dashboardData} />
                  )}

                  {message.data.confidence && (
                    <div className="confidence-info">
                      ✓ Confidence: {(message.data.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              )}

              {message.isError && (
                <div className="error-message">
                  <AlertCircle className="w-5 h-5" />
                  {message.text}
                </div>
              )}

              {message.isInfo && (
                <div className="info-message">
                  <CheckCircle className="w-5 h-5" />
                  {message.text}
                </div>
              )}
            </div>

            {message.sender === 'user' && (
              <div className="user-avatar">
                👨‍🌾
              </div>
            )}
          </div>
        ))}
        
        {/* Loading Animation */}
        {loading && (
          <div className="message-container agent">
            <div className="message-content">
              <div className="agent-header">
                <div className="agent-avatar">🤖</div>
                <span>FarMora Assistant</span>
              </div>
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <span className="typing-text">{t(currentLanguage, 'thinking') || 'Thinking...'}</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
