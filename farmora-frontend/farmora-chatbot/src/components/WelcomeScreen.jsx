import React from 'react';

const WelcomeScreen = () => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gray-900">
      <div className="w-full flex flex-col items-center">
        <h1 className="text-6xl font-bold mb-6 text-purple-400">
          FarMora
        </h1>
        <p className="text-gray-400 text-lg mb-10 transition-colors duration-300">Your Smart Farming Assistant</p>
        
        <div className="text-center max-w-2xl">
          <p className="text-gray-300 text-lg mb-6">Start typing to ask about:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-4 border border-purple-500/30 rounded-xl hover:bg-purple-500/10 cursor-pointer transition-colors bg-gray-800">
              <p className="text-sm text-purple-200">🌾 Crop diseases and remedies</p>
            </div>
            <div className="p-4 border border-purple-500/30 rounded-xl hover:bg-purple-500/10 cursor-pointer transition-colors bg-gray-800">
              <p className="text-sm text-purple-200">📅 Farm task planning</p>
            </div>
            <div className="p-4 border border-purple-500/30 rounded-xl hover:bg-purple-500/10 cursor-pointer transition-colors bg-gray-800">
              <p className="text-sm text-purple-200">🌤️ Weather & updates</p>
            </div>
            <div className="p-4 border border-purple-500/30 rounded-xl hover:bg-purple-500/10 cursor-pointer transition-colors bg-gray-800">
              <p className="text-sm text-purple-200">📊 Farm insights</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;