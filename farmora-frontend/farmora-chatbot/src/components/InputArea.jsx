import React, { useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, MessageSquare, Loader } from 'lucide-react';

const InputArea = ({ 
  inputText, 
  setInputText, 
  handleSendMessage, 
  handleMicClick, 
  handleFileSelect,
  sidebarOpen,
  loading = false
}) => {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputText]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="">
      <div className={`mx-auto px-4 py-3 ${sidebarOpen ? 'max-w-3xl' : 'max-w-5xl'}`}>
        <div className="relative">
          <div className="relative flex items-center space-x-2 bg-gray-800/80 border border-gray-700 rounded-2xl focus-within:border-purple-500 min-h-[44px] px-3.5 py-1 transition-colors shadow-lg shadow-black/20">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*"
              multiple
              className="hidden"
              disabled={loading}
            />
            
            <div className="shrink-0 p-1.5 rounded-xl flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-purple-400" />
            </div>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="shrink-0 p-1.5 hover:bg-gray-700 rounded-xl transition-colors flex items-center justify-center disabled:opacity-50"
              title="Attach image for disease detection"
              disabled={loading}
            >
              <Paperclip className="w-4 h-4 text-purple-300" />
            </button>

            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about crop diseases, tasks, weather... or upload an image"
              rows="1"
              className="flex-1 py-2 px-3 bg-transparent border-none focus:outline-none resize-none max-h-40 text-gray-100 placeholder:text-gray-500 text-base disabled:opacity-50"
              disabled={loading}
            />

            {loading ? (
              <button
                disabled
                className="shrink-0 p-1.5 bg-purple-600 rounded-xl flex items-center justify-center animate-pulse"
              >
                <Loader className="w-4 h-4 text-white animate-spin" />
              </button>
            ) : !inputText.trim() ? (
              <button
                onClick={handleMicClick}
                className="shrink-0 p-1.5 hover:bg-gray-700 rounded-xl transition-colors flex items-center justify-center"
                title="Voice input (coming soon)"
              >
                <Mic className="w-4 h-4 text-purple-300" />
              </button>
            ) : (
              <button
                onClick={handleSendMessage}
                className="shrink-0 p-1.5 bg-purple-600 hover:bg-purple-500 rounded-xl transition-colors flex items-center justify-center disabled:opacity-50"
                title="Send message (Shift+Enter for new line)"
                disabled={loading}
              >
                <Send className="w-4 h-4 text-white" />
              </button>
            )}
          </div>
        </div>
        <div className="text-xs text-center text-gray-500 mt-3">
          💡 Upload crop images for disease detection • Ask about farm tasks • Get weather & market updates
        </div>
      </div>
    </div>
  );
};

export default InputArea;
