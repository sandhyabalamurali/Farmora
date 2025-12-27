import React from 'react';
import { Plus, MessageSquare, MapPin, Leaf, TrendingUp, Calendar, LayoutDashboard, Trash2, Clock } from 'lucide-react';
import { t } from '../i18n';

const Sidebar = ({ 
  sidebarOpen, 
  startNewChat, 
  messages, 
  user, 
  currentTab, 
  setCurrentTab, 
  currentLanguage = 'en',
  chatHistory = [],
  activeChatId,
  onLoadChat,
  onDeleteChat
}) => {
  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase();
  };

  // Safe translation helper
  const translate = (key) => t(currentLanguage || 'en', key);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const tabs = [
    { id: 'chat', label: translate('chat'), icon: MessageSquare },
    { id: 'dashboard', label: translate('ai_news'), icon: TrendingUp },
    { id: 'timeline', label: translate('timeline'), icon: Calendar },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden" 
          onClick={() => {}}
        />
      )}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} fixed lg:relative z-40 h-full bg-gray-900/95 backdrop-blur-sm text-white transition-all duration-300 overflow-hidden flex flex-col border-r border-green-800/30`}>
      <div className="p-4 border-b border-green-800/30">
        <button
          onClick={startNewChat}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-lg transition-all font-medium shadow-lg shadow-green-900/30"
          data-testid="new-chat-btn"
        >
          <Plus className="w-5 h-5" />
          <span>{translate('new_chat')}</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {/* Navigation Tabs */}
        <div className="mb-4">
          <div className="text-xs font-medium text-green-500/70 px-3 py-2 uppercase tracking-wide">
            {translate('navigation')}
          </div>
          <div className="space-y-0.5">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCurrentTab(tab.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all flex items-center gap-3 ${
                    isActive
                      ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                      : 'text-gray-400 hover:bg-green-900/30 hover:text-green-300 border border-transparent'
                  }`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-green-400' : ''}`} />
                  <span className="text-sm">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Recent Chats / Chat History */}
        <div className="border-t border-green-800/30 pt-4">
          <div className="text-xs font-medium text-green-500/70 px-3 py-2 uppercase tracking-wide flex items-center justify-between">
            <span>{translate('chat_history') || 'Chat History'}</span>
            {chatHistory.length > 0 && (
              <span className="text-green-600 text-xs">{chatHistory.length}</span>
            )}
          </div>
          
          {/* Current Conversation */}
          {messages.length > 0 && (
            <div 
              className={`mx-2 mb-1 px-3 py-2 text-sm rounded-lg cursor-pointer transition-all flex items-center gap-2
                ${!activeChatId || !chatHistory.find(c => c.id === activeChatId) 
                  ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                  : 'text-gray-400 hover:bg-green-900/30 border border-transparent'}`}
            >
              <MessageSquare className="w-4 h-4 text-green-400 flex-shrink-0" />
              <span className="flex-1 truncate">{translate('current_conversation') || 'Current Chat'}</span>
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            </div>
          )}
          
          {/* Saved Chats */}
          {chatHistory.length > 0 ? (
            <div className="space-y-0.5 max-h-48 overflow-y-auto px-2">
              {chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={`group px-3 py-2 text-sm rounded-lg cursor-pointer transition-all flex items-center gap-2
                    ${activeChatId === chat.id 
                      ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                      : 'text-gray-400 hover:bg-green-900/30 border border-transparent'}`}
                  onClick={() => onLoadChat && onLoadChat(chat.id)}
                >
                  <Clock className="w-4 h-4 text-green-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm">{chat.name}</p>
                    <p className="text-xs text-gray-500">{formatDate(chat.createdAt)}</p>
                  </div>
                  {onDeleteChat && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-900/30 rounded transition-opacity"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-400" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="px-3 py-2 text-xs text-gray-500 italic">
              {translate('no_chat_history') || 'No saved chats yet'}
            </p>
          )}
        </div>
      </div>

      {/* User Profile Section */}
      {user && (
        <div className="p-4 border-t border-green-800/30">
          <div className="flex items-start space-x-3 px-2 py-2 rounded-lg bg-gray-800/40">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0 shadow-lg">
              {getInitials(user.name)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-green-300 truncate">{user.name}</div>
              <div className="text-xs text-gray-500 truncate">{user.email}</div>
              
              {user.farm_location && (
                <div className="flex items-center gap-1 text-xs text-gray-500 mt-1.5 truncate">
                  <MapPin className="w-3 h-3 flex-shrink-0 text-green-600" />
                  <span className="truncate">{user.farm_location}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
};

export default Sidebar;
