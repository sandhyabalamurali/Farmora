import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';

const LandingPage = ({ onLogin, onSignup }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950 overflow-hidden relative">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
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
            className="px-6 py-2.5 text-green-300 font-medium rounded-lg"
          >
            Login
          </button>
          <button
            onClick={onSignup}
            className="px-6 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-medium rounded-lg shadow-lg flex items-center gap-2"
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
          <div className="relative text-9xl">🌾</div>
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
          className="px-10 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-lg font-semibold rounded-xl shadow-2xl flex items-center gap-3"
        >
          <Sparkles className="w-5 h-5" />
          Start Your Journey
          <ArrowRight className="w-5 h-5" />
        </button>

        {/* Feature Pills */}
        <div className="mt-16 flex flex-wrap justify-center gap-4">
          {['🌱 Disease Detection', '📅 Smart Planning', '🌤️ Weather Insights', '📊 Market Intelligence'].map((feature, index) => (
            <div
              key={index}
              className="px-5 py-2.5 bg-gray-800/40 backdrop-blur-sm border border-green-700/30 rounded-full text-sm text-gray-300 cursor-default"
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
