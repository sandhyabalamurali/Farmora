import React, { useState, useEffect } from 'react';
import { Menu, LogOut } from 'lucide-react';
import api from './services/api';
import Sidebar from './components/Sidebar';
import WelcomeScreen from './components/WelcomeScreen';
import ChatWindow from './components/ChatWindow';
import InputArea from './components/InputArea';
import Login from './components/Login';
import Signup from './components/Signup';
import Timeline from './components/Timeline';
import Dashboard from './components/Dashboard';
import Market from './components/Market';
import './App.css';

function App() {
  const [authState, setAuthState] = useState('loading'); // loading, login, signup, authenticated
  const [user, setUser] = useState(null);
  const [currentTab, setCurrentTab] = useState('chat'); // chat, dashboard, timeline, market
  const [timelineItems, setTimelineItems] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('farmora_token');
    const savedUser = localStorage.getItem('farmora_user');

    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      setAuthState('authenticated');
    } else {
      setAuthState('login');
    }
  }, []);

  const handleLoginSuccess = (response) => {
    setUser(response);
    setAuthState('authenticated');
    setMessages([]);
    setSelectedAgent(null);
    setCurrentTab('chat');
  };

  const handleSignupSuccess = (response) => {
    setUser(response);
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

      // Determine message type based on intent
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

      // If there are planner suggestions, store them
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

  const handleMicClick = () => {
    console.log('Microphone clicked - voice processing not implemented');
    alert('Voice recording feature coming soon!');
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
      
      // Remove from pending tasks
      setPendingTasks(prev => prev.filter(t => t.task_id !== task.task_id));

      // Show confirmation message
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

  // Main app
  return (
    <div className="h-screen flex bg-gray-900">
      <Sidebar
        sidebarOpen={sidebarOpen}
        startNewChat={startNewChat}
        messages={messages}
        user={user}
      />

      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-14 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5 text-gray-300" />
            </button>
            <span className="font-bold text-2xl text-transparent bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text">
              FarMora
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{user?.name}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>

        {/* Main Area */}
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

        {/* Input Area */}
        <InputArea
          inputText={inputText}
          setInputText={setInputText}
          handleSendMessage={handleSendMessage}
          handleMicClick={handleMicClick}
          handleFileSelect={handleFileSelect}
          sidebarOpen={sidebarOpen}
          loading={loading}
        />
      </div>
    </div>
  );
}

export default App;
