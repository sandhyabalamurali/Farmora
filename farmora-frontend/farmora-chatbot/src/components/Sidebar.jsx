import React from 'react';
import { Plus, MessageSquare, MapPin, Leaf } from 'lucide-react';

const Sidebar = ({ sidebarOpen, startNewChat, messages, user, currentTab, setCurrentTab }) => {
  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase();
  };

  return (
    <div className={`${sidebarOpen ? 'w-64' : 'w-0'} bg-gray-800 text-white transition-all duration-300 overflow-hidden flex flex-col border-r border-gray-700`}>
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={startNewChat}
          className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 rounded-lg transition-all duration-200 font-medium"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="px-3 py-2">
          <button onClick={() => setCurrentTab('chat')} className={`w-full text-left px-3 py-2 rounded-lg mb-2 ${currentTab==='chat'?'bg-gray-700':''}`}>Chat</button>
          <button onClick={() => setCurrentTab('dashboard')} className={`w-full text-left px-3 py-2 rounded-lg mb-2 ${currentTab==='dashboard'?'bg-gray-700':''}`}>Dashboard</button>
          <button onClick={() => setCurrentTab('timeline')} className={`w-full text-left px-3 py-2 rounded-lg ${currentTab==='timeline'?'bg-gray-700':''}`}>Timeline</button>
        </div>
        {messages.length > 0 && (
          <>
            <div className="text-xs font-semibold text-gray-500 px-3 py-2 uppercase tracking-wider">Today</div>
            <div className="px-3 py-2.5 text-sm text-gray-300 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors">
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Current conversation
            </div>
          </>
        )}
      </div>

      {/* User Profile Section */}
      {user && (
        <div className="p-4 border-t border-gray-700 bg-gray-900/50">
          <div className="flex items-start space-x-3 px-3 py-2.5 rounded-lg hover:bg-gray-700 transition-colors">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0">
              {getInitials(user.name)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-gray-200 truncate">{user.name}</div>
              <div className="text-xs text-gray-400 truncate">{user.email}</div>
              
              {user.farm_location && (
                <div className="flex items-center gap-1 text-xs text-gray-400 mt-1 truncate">
                  <MapPin className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">{user.farm_location}</span>
                </div>
              )}
              
              {user.crops && user.crops.length > 0 && (
                <div className="flex items-center gap-1 text-xs text-gray-400 mt-1 truncate">
                  <Leaf className="w-3 h-3 flex-shrink-0" />
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
