import React, { useState, useEffect } from 'react';
import { Menu, LogOut, Globe } from 'lucide-react';
import api from './services/api';
import Sidebar from './components/Sidebar';
import WelcomeScreen from './components/WelcomeScreen';
import ChatWindow from './components/ChatWindow';
import InputArea from './components/InputArea';
import Login from './components/Login';
import Signup from './components/Signup';
import Timeline from './components/Timeline';
import Dashboard from './components/Dashboard';
import './App.css';

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिंदी' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'gu', name: 'ગુજરાતી' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'ml', name: 'മലയാളം' },
  { code: 'mr', name: 'मराठी' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'te', name: 'తెలుగు' },
  { code: 'ur', name: 'اردو' }
];

function App() {
  const [authState, setAuthState] = useState('loading');
  const [user, setUser] = useState(null);
  const [currentTab, setCurrentTab] = useState('chat');
  const [timelineItems, setTimelineItems] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('farmora_token');
    const savedUser = localStorage.getItem('farmora_user');

    if (token && savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      setCurrentLanguage(userData.language || 'en');
      setAuthState('authenticated');
    } else {
      setAuthState('login');
    }
  }, []);

  const handleLoginSuccess = (response) => {
    setUser(response);
    setCurrentLanguage(response.language || 'en');
    setAuthState('authenticated');
    setMessages([]);
    setSelectedAgent(null);
    setCurrentTab('chat');
  };

  const handleSignupSuccess = (response) => {
    setUser(response);
    setCurrentLanguage(response.language || 'en');
    setAuthState('authenticated');
    setMessages([]);
    setSelectedAgent(null);
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
    setAuthState('login');
    setMessages([]);
    setSelectedAgent(null);
    setPendingTasks([]);
    setCurrentLanguage('en');
  };

  const handleLanguageChange = async (langCode) => {
    setCurrentLanguage(langCode);
    setShowLanguageDropdown(false);
    
    // Update user profile with new language
    try {
      await api.updateProfile({ language: langCode });
      const savedUser = localStorage.getItem('farmora_user');
      if (savedUser) {
        const userData = JSON.parse(savedUser);
        userData.language = langCode;
        localStorage.setItem('farmora_user', JSON.stringify(userData));
      }
    } catch (error) {
      console.error('Failed to update language preference:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      agent: selectedAgent,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const response = await api.sendMessage(
        user.user_id,
        inputText,
        null,
        null
      );

      const agentMessage = {
        id: Date.now() + 1,
        text: response.ai_response,
        sender: 'agent',
        agent: selectedAgent,
        timestamp: new Date(),
        intent: response.intent,
        data: {
          diseaseResult: response.disease_result,
          plannerSuggestions: response.planner_suggestions,
          dashboardData: response.dashboard_data,
          confidence: response.confidence_score
        }
      };

      setMessages(prev => [...prev, agentMessage]);

      if (response.planner_suggestions && response.planner_suggestions.length > 0) {
        setPendingTasks(response.planner_suggestions);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: `❌ Error: ${error.message}. Please try again.`,
        sender: 'agent',
        agent: selectedAgent,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceTranscription = async (audioBlob) => {
    try {
      const result = await api.transcribeVoice(audioBlob, 'recording.webm');
      if (result.success && result.text) {
        setInputText(result.text);
      } else {
        throw new Error('No transcription result');
      }
    } catch (error) {
      console.error('Transcription error:', error);
      throw error;
    }
  };

  const handleMicClick = () => {
    // This is now handled by the InputArea component
    console.log('Microphone click handled by InputArea');
  };

  const handleImageUpload = async (files) => {
    if (files.length === 0) return;

    const file = files[0];
    const reader = new FileReader();

    reader.onload = async (e) => {
      const base64Image = e.target.result;
      const caption = `Image uploaded: ${file.name}`;

      const userMessage = {
        id: Date.now(),
        text: caption,
        sender: 'user',
        agent: selectedAgent,
        timestamp: new Date(),
        image: base64Image
      };

      setMessages(prev => [...prev, userMessage]);
      setLoading(true);

      try {
        const response = await api.sendMessage(
          user.user_id,
          'Please analyze this crop image',
          base64Image,
          caption
        );

        const agentMessage = {
          id: Date.now() + 1,
          text: response.ai_response,
          sender: 'agent',
          agent: 'disease_detector',
          timestamp: new Date(),
          intent: response.intent,
          data: {
            diseaseResult: response.disease_result,
            plannerSuggestions: response.planner_suggestions,
            dashboardData: response.dashboard_data,
            confidence: response.confidence_score
          }
        };

        setMessages(prev => [...prev, agentMessage]);

        if (response.planner_suggestions && response.planner_suggestions.length > 0) {
          setPendingTasks(response.planner_suggestions);
        }
      } catch (error) {
        const errorMessage = {
          id: Date.now() + 1,
          text: `❌ Image analysis failed: ${error.message}`,
          sender: 'agent',
          timestamp: new Date(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setLoading(false);
      }
    };

    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleImageUpload(files);
    }
  };

  const handleTaskConfirmation = async (task, confirmed) => {
    try {
      const response = await api.confirmTask(task.task_id, user.user_id, confirmed);
      
      setPendingTasks(prev => prev.filter(t => t.task_id !== task.task_id));

      const confirmMessage = {
        id: Date.now(),
        text: response.message,
        sender: 'agent',
        timestamp: new Date(),
        isInfo: true
      };

      setMessages(prev => [...prev, confirmMessage]);
      
      // Refresh timeline after confirmation
      try {
        const timeline = await api.getTimeline(user.user_id);
        setTimelineItems(timeline.timeline || []);
      } catch (e) {
        console.error('Failed to refresh timeline', e);
      }
    } catch (error) {
      alert(`Confirmation failed: ${error.message}`);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setPendingTasks([]);
  };

  // Auth screens
  if (authState === 'login') {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToSignup={() => setAuthState('signup')}
      />
    );
  }

  if (authState === 'signup') {
    return (
      <Signup
        onSignupSuccess={handleSignupSuccess}
        onSwitchToLogin={() => setAuthState('login')}
      />
    );
  }

  const currentLangName = LANGUAGES.find(l => l.code === currentLanguage)?.name || 'English';

  // Main app
  return (
    <div className="h-screen flex bg-gradient-to-br from-green-950 via-gray-900 to-emerald-950">
      <Sidebar
        sidebarOpen={sidebarOpen}
        startNewChat={startNewChat}
        messages={messages}
        user={user}
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
      />

      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-16 bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-b border-green-800/30 backdrop-blur-sm flex items-center justify-between px-6 shadow-lg">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-green-800/40 rounded-lg transition-all duration-200 border border-green-700/30"
              data-testid="toggle-sidebar-btn"
            >
              <Menu className="w-5 h-5 text-green-300" />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-3xl">🌾</span>
              <span className="font-bold text-3xl text-transparent bg-gradient-to-r from-green-400 via-emerald-400 to-green-500 bg-clip-text drop-shadow-lg">
                FarMora
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <div className="relative">
              <button
                onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
                className="flex items-center gap-2 px-3 py-2 bg-green-900/30 hover:bg-green-800/40 rounded-lg border border-green-700/30 transition-all"
                data-testid="language-switcher-btn"
              >
                <Globe className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-300">{currentLangName}</span>
              </button>
              
              {showLanguageDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-gray-800 border border-green-700/30 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
                  {LANGUAGES.map(lang => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-green-800/40 transition-colors ${
                        currentLanguage === lang.code 
                          ? 'bg-green-700/30 text-green-300' 
                          : 'text-gray-300'
                      }`}
                    >
                      {lang.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 px-3 py-2 bg-green-900/30 rounded-lg border border-green-700/30">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-300 font-medium">{user?.name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200 border border-red-700/30 hover:border-red-600/50"
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>

        {/* Click outside to close language dropdown */}
        {showLanguageDropdown && (
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setShowLanguageDropdown(false)}
          />
        )}

        {/* Main Content Area */}
        {currentTab === 'dashboard' && <Dashboard user={user} />}
        {currentTab === 'timeline' && <Timeline user={user} items={timelineItems} />}
        {currentTab === 'chat' && (
          (messages.length === 0) ? (
            <WelcomeScreen />
          ) : (
            <ChatWindow
              messages={messages}
              pendingTasks={pendingTasks}
              onTaskConfirmation={handleTaskConfirmation}
            />
          )
        )}

        {/* Input Area - Only show for chat tab */}
        {currentTab === 'chat' && (
          <InputArea
            inputText={inputText}
            setInputText={setInputText}
            handleSendMessage={handleSendMessage}
            handleMicClick={handleMicClick}
            handleFileSelect={handleFileSelect}
            sidebarOpen={sidebarOpen}
            loading={loading}
            onVoiceTranscription={handleVoiceTranscription}
          />
        )}
      </div>
    </div>
  );
}

export default App;
