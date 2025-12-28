import React, { useState, useEffect, useRef } from 'react';
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
import LandingPage from './components/LandingPage';
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
  const timelineRef = useRef(null); // Ref for Timeline component
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  // Language defaults to user's preferred language (set after login)
  const [currentLanguage, setCurrentLanguage] = useState(null);
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);
  
  // Chat history state
  const [chatHistory, setChatHistory] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  // Get storage key for current user's chat history
  const getChatHistoryKey = (userId) => `farmora_chat_history_${userId}`;

  // Load chat history from localStorage when user changes
  useEffect(() => {
    if (user?.user_id) {
      const savedHistory = localStorage.getItem(getChatHistoryKey(user.user_id));
      if (savedHistory) {
        try {
          setChatHistory(JSON.parse(savedHistory));
        } catch (e) {
          console.error('Failed to load chat history:', e);
          setChatHistory([]);
        }
      } else {
        setChatHistory([]);
      }
    }
  }, [user?.user_id]);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (user?.user_id && chatHistory.length > 0) {
      localStorage.setItem(getChatHistoryKey(user.user_id), JSON.stringify(chatHistory));
    }
  }, [chatHistory, user?.user_id]);

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
      setAuthState('landing');
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
      const result = await api.transcribeVoice(audioBlob, 'recording.webm', currentLanguage);
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
      
      // Trigger timeline refresh if component is mounted and task was confirmed
      if (confirmed && timelineRef.current) {
        // Small delay to allow backend to process
        setTimeout(() => {
          timelineRef.current?.refresh();
        }, 500);
      }
    } catch (error) {
      alert(`Confirmation failed: ${error.message}`);
    }
  };

  const startNewChat = () => {
    // Save current chat to history if it has messages
    if (messages.length > 0) {
      const chatName = generateChatName(messages);
      const newChatEntry = {
        id: activeChatId || Date.now(),
        name: chatName,
        messages: messages,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      // Update existing chat or add new one
      setChatHistory(prev => {
        const existingIndex = prev.findIndex(c => c.id === activeChatId);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = newChatEntry;
          return updated;
        }
        // Keep only last 10 chats
        const newHistory = [newChatEntry, ...prev].slice(0, 10);
        return newHistory;
      });
    }
    
    // Clear current chat
    setMessages([]);
    setPendingTasks([]);
    setActiveChatId(Date.now());
  };

  // Generate a name for the chat based on its content
  const generateChatName = (msgs) => {
    // Find the first user message
    const firstUserMsg = msgs.find(m => m.sender === 'user');
    if (firstUserMsg) {
      // Truncate to 30 chars
      const text = firstUserMsg.text || 'New Chat';
      return text.length > 30 ? text.substring(0, 30) + '...' : text;
    }
    return `Chat ${new Date().toLocaleDateString()}`;
  };

  // Load a previous chat from history
  const loadChat = (chatId) => {
    // Save current chat first if it has messages
    if (messages.length > 0 && activeChatId !== chatId) {
      const chatName = generateChatName(messages);
      const currentChat = {
        id: activeChatId || Date.now(),
        name: chatName,
        messages: messages,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      setChatHistory(prev => {
        const existingIndex = prev.findIndex(c => c.id === activeChatId);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = currentChat;
          return updated;
        }
        return [currentChat, ...prev].slice(0, 10);
      });
    }
    
    // Load the selected chat
    const selectedChat = chatHistory.find(c => c.id === chatId);
    if (selectedChat) {
      setMessages(selectedChat.messages);
      setActiveChatId(chatId);
      setPendingTasks([]);
    }
  };

  // Delete a chat from history
  const deleteChat = (chatId) => {
    setChatHistory(prev => {
      const newHistory = prev.filter(c => c.id !== chatId);
      // Update localStorage immediately
      if (user?.user_id) {
        if (newHistory.length > 0) {
          localStorage.setItem(getChatHistoryKey(user.user_id), JSON.stringify(newHistory));
        } else {
          localStorage.removeItem(getChatHistoryKey(user.user_id));
        }
      }
      return newHistory;
    });
    if (activeChatId === chatId) {
      setMessages([]);
      setActiveChatId(null);
    }
  };

  // Get available languages (preferred language first, then English)
  const getAvailableLanguages = () => {
    const preferredLang = user?.language || 'en';
    // If preferred is English, just return English
    if (preferredLang === 'en') {
      return LANGUAGES.filter(l => l.code === 'en');
    }
    // Otherwise return preferred language first, then English
    const preferred = LANGUAGES.find(l => l.code === preferredLang);
    const english = LANGUAGES.find(l => l.code === 'en');
    return [preferred, english].filter(Boolean);
  };

  // Get current language display name
  const getCurrentLanguageName = () => {
    const lang = LANGUAGES.find(l => l.code === (currentLanguage || user?.language || 'en'));
    return lang?.name || 'English';
  };

  // Auth screens - Login and Signup as full pages
  if (authState === 'landing') {
    return (
      <LandingPage 
        onLogin={() => setAuthState('login')}
        onSignup={() => setAuthState('signup')}
      />
    );
  }

  if (authState === 'login') {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToSignup={() => setAuthState('signup')}
        onClose={() => setAuthState('landing')}
        isModal={false}
      />
    );
  }

  if (authState === 'signup') {
    return (
      <Signup
        onSignupSuccess={handleSignupSuccess}
        onSwitchToLogin={() => setAuthState('login')}
        onClose={() => setAuthState('landing')}
        isModal={false}
      />
    );
  }

  // Get the effective language (use preferred if currentLanguage not set)
  const effectiveLanguage = currentLanguage || user?.language || 'en';
  const currentLangName = LANGUAGES.find(l => l.code === effectiveLanguage)?.name || 'English';

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
        currentLanguage={effectiveLanguage}
        chatHistory={chatHistory}
        activeChatId={activeChatId}
        onLoadChat={loadChat}
        onDeleteChat={deleteChat}
      />

      <div className="flex-1 flex flex-col">
        {/* Top Bar - Premium Design */}
        <div className="h-14 bg-gray-900/80 backdrop-blur-sm border-b border-green-800/30 flex items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-green-900/30 rounded-lg transition-colors"
              data-testid="toggle-sidebar-btn"
            >
              <Menu className="w-5 h-5 text-green-400" />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xl">🌾</span>
              <span className="font-bold text-lg text-transparent bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text">
                FarMora
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Switcher */}
            <div className="relative">
              <button
                onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/60 hover:bg-green-900/40 rounded-lg border border-green-700/30 transition-colors"
                data-testid="language-switcher-btn"
              >
                <Globe className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-300 hidden sm:inline">{currentLangName}</span>
              </button>
              
              {showLanguageDropdown && (
                <>
                  {/* Backdrop */}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowLanguageDropdown(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-gray-900/95 backdrop-blur-sm border border-green-700/30 rounded-lg shadow-xl shadow-green-900/20 z-50 overflow-hidden">
                    <div className="p-1">
                      {getAvailableLanguages().map(lang => (
                        <button
                          key={lang.code}
                          onClick={() => handleLanguageChange(lang.code)}
                          className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors flex items-center justify-between ${
                            effectiveLanguage === lang.code 
                              ? 'bg-green-500/20 text-green-300' 
                              : 'text-gray-300 hover:bg-green-900/30'
                          }`}
                        >
                          <span>{lang.name}</span>
                          {effectiveLanguage === lang.code && (
                            <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* User Name */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gray-800/60 rounded-lg border border-green-700/30">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-300">{user?.name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-green-700/30 hover:border-red-500/50"
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        {currentTab === 'dashboard' && <Dashboard user={user} currentLanguage={effectiveLanguage} />}
        {currentTab === 'timeline' && <Timeline ref={timelineRef} user={user} currentLanguage={effectiveLanguage} />}
        {currentTab === 'chat' && (
          (messages.length === 0 && !loading) ? (
            <WelcomeScreen />
          ) : (
            <ChatWindow
              messages={messages}
              pendingTasks={pendingTasks}
              onTaskConfirmation={handleTaskConfirmation}
              currentLanguage={effectiveLanguage}
              loading={loading}
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
            currentLanguage={effectiveLanguage}
          />
        )}
      </div>
    </div>
  );
}

export default App;
