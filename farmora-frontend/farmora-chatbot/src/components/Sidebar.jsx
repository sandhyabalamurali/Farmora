import React from 'react';
import { Plus, MessageSquare, MapPin, Leaf, TrendingUp, Calendar, LayoutDashboard } from 'lucide-react';

const Sidebar = ({ sidebarOpen, startNewChat, messages, user, currentTab, setCurrentTab }) => {
  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase();
  };

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'market', label: 'Market', icon: TrendingUp },
    { id: 'timeline', label: 'Timeline', icon: Calendar },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  ];

  return (
    <div className={`${sidebarOpen ? 'w-72' : 'w-0'} bg-gradient-to-b from-green-900/30 to-gray-900/50 backdrop-blur-sm text-white transition-all duration-300 overflow-hidden flex flex-col border-r border-green-800/30 shadow-2xl`}>
      <div className="p-4 border-b border-green-800/30">
        <button
          onClick={startNewChat}
          className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-lg transition-all duration-200 font-medium shadow-lg hover:shadow-green-500/50"
          data-testid="new-chat-btn"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {/* Navigation Tabs */}
        <div className="mb-4">
          <div className="text-xs font-semibold text-green-400 px-3 py-2 uppercase tracking-wider">
            Navigation
          </div>
          <div className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCurrentTab(tab.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-all duration-200 flex items-center gap-3 group ${
                    isActive
                      ? 'bg-gradient-to-r from-green-700/50 to-emerald-700/50 border border-green-600/50 shadow-md'
                      : 'hover:bg-green-900/30 border border-transparent hover:border-green-700/30'
                  }`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-green-300' : 'text-gray-400 group-hover:text-green-400'}`} />
                  <span className={`font-medium ${isActive ? 'text-green-100' : 'text-gray-300 group-hover:text-green-200'}`}>
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Recent Chats */}
        {messages.length > 0 && (
          <>
            <div className="text-xs font-semibold text-green-400 px-3 py-2 uppercase tracking-wider border-t border-green-900/30 pt-4">
              Recent
            </div>
            <div className="px-3 py-2.5 text-sm text-gray-300 hover:bg-green-900/30 rounded-lg cursor-pointer transition-all duration-200 flex items-center gap-2 border border-transparent hover:border-green-700/30">
              <MessageSquare className="w-4 h-4 text-green-400" />
              Current conversation
            </div>
          </>
        )}
      </div>

      {/* User Profile Section */}
      {user && (
        <div className="p-4 border-t border-green-800/30 bg-gradient-to-br from-green-900/20 to-gray-900/40">
          <div className="flex items-start space-x-3 px-3 py-3 rounded-lg hover:bg-green-900/30 transition-all duration-200 border border-transparent hover:border-green-700/30">
            <div className="w-11 h-11 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 shadow-md">
              {getInitials(user.name)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-green-100 truncate">{user.name}</div>
              <div className="text-xs text-gray-400 truncate">{user.email}</div>
              
              {user.farm_location && (
                <div className="flex items-center gap-1 text-xs text-gray-400 mt-1.5 truncate">
                  <MapPin className="w-3 h-3 flex-shrink-0 text-green-400" />
                  <span className="truncate">{user.farm_location}</span>
                </div>
              )}
              
              {user.crops && user.crops.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-gray-400 mt-1 truncate">
                  <Leaf className="w-3 h-3 flex-shrink-0 text-green-400" />
                  <span className="truncate">{user.crops.join(', ')}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
