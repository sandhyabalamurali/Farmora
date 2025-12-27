import { MessageSquare, Calendar, TrendingUp, X } from 'lucide-react';

const AgentMenu = ({ selectedAgent, selectAgent, setShowAgentMenu }) => {
  return (
    <div className="absolute bottom-full left-0 mb-3 bg-gray-800 border border-gray-700 rounded-xl overflow-hidden w-72 z-50">
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <span className="font-semibold text-gray-200">Select Agent</span>
        <button onClick={() => setShowAgentMenu(false)} className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors">
          <X className="w-4 h-4 text-gray-400" />
        </button>
      </div>
      
      <div className="p-2">
        <button
          onClick={() => selectAgent(null)}
          className={`w-full flex items-center space-x-3 p-3.5 rounded-lg transition-colors ${
            selectedAgent === null ? 'bg-purple-500/20 border border-purple-500' : 'hover:bg-gray-700 border border-transparent'
          }`}
        >
          <div className={`w-11 h-11 ${selectedAgent === null ? 'bg-purple-500' : 'bg-purple-500/20'} rounded-lg flex items-center justify-center shrink-0`}>
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 text-left">
            <div className="font-medium text-gray-200">General Chat</div>
            <div className="text-xs text-gray-400">No specific agent</div>
          </div>
        </button>

        <button
          onClick={() => selectAgent('timeline')}
          className={`w-full flex items-center space-x-3 p-3.5 rounded-lg transition-colors mt-2 ${
            selectedAgent === 'timeline' ? 'bg-purple-500/20 border border-purple-500' : 'hover:bg-gray-700 border border-transparent'
          }`}
        >
          <div className={`w-11 h-11 ${selectedAgent === 'timeline' ? 'bg-purple-500' : 'bg-purple-500/20'} rounded-lg flex items-center justify-center shrink-0`}>
            <Calendar className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 text-left">
            <div className="font-medium text-gray-200">Timeline Agent</div>
            <div className="text-xs text-gray-400">Schedule & tasks</div>
          </div>
        </button>

        <button
          onClick={() => selectAgent('marketprice')}
          className={`w-full flex items-center space-x-3 p-3.5 rounded-lg transition-colors mt-2 ${
            selectedAgent === 'marketprice' ? 'bg-purple-500/20 border border-purple-500' : 'hover:bg-gray-700 border border-transparent'
          }`}
        >
          <div className={`w-11 h-11 ${selectedAgent === 'marketprice' ? 'bg-purple-500' : 'bg-purple-500/20'} rounded-lg flex items-center justify-center shrink-0`}>
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 text-left">
            <div className="font-medium text-gray-200">Market Price Agent</div>
            <div className="text-xs text-gray-400">Prices & insights</div>
          </div>
        </button>
      </div>
    </div>
  );
};

export default AgentMenu;