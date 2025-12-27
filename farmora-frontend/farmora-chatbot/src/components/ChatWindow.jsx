import React, { useRef, useEffect } from 'react';
import { MessageSquare, AlertCircle, CheckCircle, Leaf, Droplet, Bug, Thermometer, Wind } from 'lucide-react';
import './ChatWindow.css';

const ChatWindow = ({ messages, pendingTasks, onTaskConfirmation }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
            <span className="confidence-badge">{disease.confidence.toFixed(0)}% confident</span>
          </h4>
          <div className={`severity-tag severity-${disease.severity}`}>
            {disease.severity.toUpperCase()}
          </div>
        </div>

        <div className="disease-content">
          <div className="disease-section">
            <h5>💊 Remedy</h5>
            <p>{disease.remedy}</p>
          </div>

          <div className="disease-tips">
            <h5>🛡️ Prevention Tips</h5>
            <ul>
              {disease.prevention_tips?.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>

          {disease.immediate_action && (
            <div className="disease-action">
              <AlertCircle className="w-4 h-4" />
              <span><strong>Immediate Action:</strong> {disease.immediate_action}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const PlannerCard = ({ task, onConfirmation }) => {
    if (!task) return null;

    return (
      <div className="planner-card">
        <div className="planner-header">
          <h4>📅 {task.task_name}</h4>
          <span className={`priority-tag priority-${task.priority}`}>
            {task.priority.toUpperCase()}
          </span>
        </div>

        <div className="planner-content">
          <p className="task-date">📆 {task.date}</p>
          <p className="task-reason">💡 {task.reason}</p>
          
          {task.description && (
            <p className="task-description">{task.description}</p>
          )}

          {task.estimated_hours && (
            <p className="task-time">⏱️ Estimated: {task.estimated_hours} hours</p>
          )}

          {task.safety_notes && (
            <div className="safety-notes">
              ⚠️ <strong>Safety:</strong> {task.safety_notes}
            </div>
          )}

          {task.requires_confirmation && (
            <div className="task-actions">
              <button
                onClick={() => onConfirmation(task, true)}
                className="btn-confirm"
              >
                ✓ Accept Task
              </button>
              <button
                onClick={() => onConfirmation(task, false)}
                className="btn-reject"
              >
                ✕ Decline
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const DashboardCard = ({ data }) => {
    if (!data) return null;

    return (
      <div className="dashboard-card">
        <h4>📊 Farm Dashboard</h4>

        {data.weather && (
          <div className="weather-section">
            <h5>🌤️ Weather & Forecast</h5>
            <p>{data.weather}</p>
          </div>
        )}

        {data.market_news && data.market_news.length > 0 && (
          <div className="news-section">
            <h5>📰 Market Updates</h5>
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
                  <p>{message.text}</p>
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
                      <h4>📋 Suggested Farm Tasks</h4>
                      {message.data.plannerSuggestions.map((task, idx) => (
                        <PlannerCard
                          key={idx}
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
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
