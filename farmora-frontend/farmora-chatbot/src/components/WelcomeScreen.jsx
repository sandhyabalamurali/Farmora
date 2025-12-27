import React from 'react';
import { Sprout, Calendar, Cloud, TrendingUp } from 'lucide-react';

const WelcomeScreen = () => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-green-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl"></div>
      </div>
      
      <div className="w-full flex flex-col items-center relative z-10">
        {/* Logo & Title */}
        <div className="mb-8 text-center">
          <div className="relative inline-block">
            <div className="absolute inset-0 bg-green-500/20 blur-2xl rounded-full scale-150"></div>
            <div className="relative text-6xl mb-4">🌾</div>
          </div>
          <h1 className="text-4xl font-bold mb-3 text-transparent bg-gradient-to-r from-green-400 via-emerald-300 to-green-500 bg-clip-text">
            FarMora
          </h1>
          <p className="text-gray-400 text-lg">
            Your AI-Powered Farming Assistant
          </p>
        </div>
        
        <div className="text-center max-w-3xl">
          <p className="text-green-400 text-base mb-8 font-medium">
            How can I help you today?
          </p>
          
          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="group p-5 border border-green-700/30 rounded-xl hover:bg-green-900/20 hover:border-green-600/50 cursor-pointer transition-all duration-300 bg-gray-800/30 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-green-900/40 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-800/60 transition-colors">
                  <Sprout className="w-5 h-5 text-green-400" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-green-200 mb-1">
                    Crop Diseases & Remedies
                  </h3>
                  <p className="text-xs text-gray-400">
                    Upload images to detect diseases and get treatment recommendations
                  </p>
                </div>
              </div>
            </div>

            <div className="group p-5 border border-green-700/30 rounded-xl hover:bg-green-900/20 hover:border-green-600/50 cursor-pointer transition-all duration-300 bg-gray-800/30 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-green-900/40 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-800/60 transition-colors">
                  <Calendar className="w-5 h-5 text-green-400" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-green-200 mb-1">
                    Farm Task Planning
                  </h3>
                  <p className="text-xs text-gray-400">
                    Get personalized task schedules and reminders for your crops
                  </p>
                </div>
              </div>
            </div>

            <div className="group p-5 border border-green-700/30 rounded-xl hover:bg-green-900/20 hover:border-green-600/50 cursor-pointer transition-all duration-300 bg-gray-800/30 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-green-900/40 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-800/60 transition-colors">
                  <Cloud className="w-5 h-5 text-green-400" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-green-200 mb-1">
                    Weather Insights
                  </h3>
                  <p className="text-xs text-gray-400">
                    Get weather forecasts and farming recommendations
                  </p>
                </div>
              </div>
            </div>

            <div className="group p-5 border border-green-700/30 rounded-xl hover:bg-green-900/20 hover:border-green-600/50 cursor-pointer transition-all duration-300 bg-gray-800/30 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-green-900/40 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-800/60 transition-colors">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-green-200 mb-1">
                    Market Intelligence
                  </h3>
                  <p className="text-xs text-gray-400">
                    Access latest market news and price trends
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Hint */}
          <div className="mt-10 p-4 bg-green-900/20 rounded-lg border border-green-700/30 inline-block">
            <p className="text-sm text-green-300">
              💬 Type your question below or upload a crop image to get started
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;