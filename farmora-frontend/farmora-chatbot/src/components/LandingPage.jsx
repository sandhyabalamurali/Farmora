import React from 'react';
import { Leaf, ArrowRight, Sparkles } from 'lucide-react';

const LandingPage = ({ onLogin, onSignup }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 overflow-hidden relative">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Floating leaves animation */}
        <div className="absolute top-10 left-10 text-6xl opacity-20 animate-pulse">🍃</div>
        <div className="absolute top-1/4 right-20 text-5xl opacity-15 animate-bounce">🌾</div>
        <div className="absolute bottom-1/3 left-1/4 text-7xl opacity-10 animate-pulse delay-200">🌱</div>
        <div className="absolute top-1/2 right-1/3 text-4xl opacity-20 animate-bounce delay-500">🌿</div>
        <div className="absolute bottom-20 right-10 text-6xl opacity-15 animate-pulse delay-300">🍂</div>
        <div className="absolute top-20 left-1/3 text-5xl opacity-10 animate-bounce delay-700">🌻</div>
        
        {/* Gradient overlays */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-green-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-green-600/5 rounded-full blur-3xl"></div>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-3">
          <span className="text-4xl">🌾</span>
          <span className="font-bold text-3xl text-transparent bg-gradient-to-r from-green-400 via-emerald-400 to-green-500 bg-clip-text">
            FarMora
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={onLogin}
            className="px-6 py-2.5 text-green-300 hover:text-green-200 font-medium transition-all duration-300 hover:bg-green-900/30 rounded-lg"
          >
            Login
          </button>
          <button
            onClick={onSignup}
            className="px-6 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-medium rounded-lg transition-all duration-300 shadow-lg hover:shadow-green-500/30 flex items-center gap-2"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-100px)] px-8 text-center">
        {/* Main Logo */}
        <div className="mb-8 relative">
          <div className="absolute inset-0 bg-green-500/20 blur-3xl rounded-full scale-150"></div>
          <div className="relative text-9xl animate-pulse">🌾</div>
        </div>

        {/* Brand Name */}
        <h1 className="text-7xl md:text-8xl font-bold mb-6 text-transparent bg-gradient-to-r from-green-400 via-emerald-300 to-green-500 bg-clip-text drop-shadow-2xl">
          FarMora
        </h1>

        {/* Tagline */}
        <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-2xl font-light">
          <span className="text-green-400">AI-Powered</span> Farming Intelligence
        </p>

        {/* CTA Button */}
        <button
          onClick={onSignup}
          className="group relative px-10 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white text-lg font-semibold rounded-xl transition-all duration-300 shadow-2xl hover:shadow-green-500/40 transform hover:scale-105 flex items-center gap-3"
        >
          <Sparkles className="w-5 h-5" />
          Start Your Journey
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </button>

        {/* Feature Pills */}
        <div className="mt-16 flex flex-wrap justify-center gap-4">
          {['🌱 Disease Detection', '📅 Smart Planning', '🌤️ Weather Insights', '📊 Market Intelligence'].map((feature, index) => (
            <div
              key={index}
              className="px-5 py-2.5 bg-gray-800/40 backdrop-blur-sm border border-green-700/30 rounded-full text-sm text-gray-300 hover:border-green-500/50 hover:text-green-300 transition-all duration-300 cursor-default"
            >
              {feature}
            </div>
          ))}
        </div>

        {/* Floating Visual Elements */}
        <div className="absolute bottom-10 left-0 right-0 flex justify-center gap-8 opacity-30">
          <div className="w-32 h-1 bg-gradient-to-r from-transparent via-green-500 to-transparent rounded-full"></div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 text-center py-6 text-gray-500 text-sm">
        <p>Empowering Indian Farmers with AI</p>
      </footer>
    </div>
  );
};

export default LandingPage;
