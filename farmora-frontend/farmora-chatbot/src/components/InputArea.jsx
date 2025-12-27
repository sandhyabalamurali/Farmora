import React, { useRef, useEffect, useState } from 'react';
import { Send, Mic, MicOff, Paperclip, MessageSquare, Loader, Square } from 'lucide-react';
import { t } from '../i18n';

const InputArea = ({ 
  inputText, 
  setInputText, 
  handleSendMessage, 
  handleMicClick, 
  handleFileSelect,
  sidebarOpen,
  loading = false,
  onVoiceTranscription,
  currentLanguage = 'en'
}) => {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputText]);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        
        if (onVoiceTranscription && audioBlob.size > 0) {
          setIsTranscribing(true);
          try {
            await onVoiceTranscription(audioBlob);
          } catch (error) {
            console.error('Transcription error:', error);
            alert('Voice transcription failed. Please try again.');
          } finally {
            setIsTranscribing(false);
          }
        }
      };

      mediaRecorder.start(100);
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      if (error.name === 'NotAllowedError') {
        alert(t(currentLanguage, 'microphone_denied'));
      } else {
        alert(t(currentLanguage, 'microphone_error'));
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleMicButtonClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="bg-gray-900/80 backdrop-blur-sm border-t border-green-800/30">
      <div className={`mx-auto px-4 py-3 ${sidebarOpen ? 'max-w-3xl' : 'max-w-5xl'}`}>
        <div className="relative">
          <div className={`relative flex items-center space-x-2 ${isRecording ? 'bg-red-900/20 border-red-500/50' : 'bg-gray-800/60 border-green-700/30'} border rounded-xl focus-within:border-green-500 min-h-[44px] px-3 py-1 transition-colors`}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*"
              multiple
              className="hidden"
              disabled={loading || isRecording}
            />
            
            <div className="shrink-0 p-1.5 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-green-400" />
            </div>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="shrink-0 p-1.5 hover:bg-green-900/30 rounded-lg transition-colors flex items-center justify-center disabled:opacity-50"
              title={t(currentLanguage, 'upload_image')}
              disabled={loading || isRecording}
            >
              <Paperclip className="w-4 h-4 text-green-400" />
            </button>

            {isRecording ? (
              <div className="flex-1 flex items-center gap-3 py-2 px-3">
                <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-red-400 font-medium text-sm">{t(currentLanguage, 'recording')} {formatTime(recordingTime)}</span>
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t(currentLanguage, 'ask_placeholder')}
                rows="1"
                className="flex-1 py-2 px-2 bg-transparent border-none focus:outline-none resize-none max-h-40 text-gray-100 placeholder:text-gray-500 text-sm disabled:opacity-50"
                disabled={loading || isTranscribing}
              />
            )}

            {loading || isTranscribing ? (
              <button
                disabled
                className="shrink-0 p-1.5 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg flex items-center justify-center"
                title={isTranscribing ? t(currentLanguage, 'transcribing') : t(currentLanguage, 'processing')}
              >
                <Loader className="w-4 h-4 text-white animate-spin" />
              </button>
            ) : isRecording ? (
              <button
                onClick={stopRecording}
                className="shrink-0 p-2 bg-red-600 hover:bg-red-500 rounded-lg transition-colors flex items-center justify-center"
                title={t(currentLanguage, 'stop_recording')}
              >
                <Square className="w-4 h-4 text-white" />
              </button>
            ) : !inputText.trim() ? (
              <button
                onClick={handleMicButtonClick}
                className="shrink-0 p-1.5 hover:bg-green-900/30 rounded-lg transition-colors flex items-center justify-center"
                title={t(currentLanguage, 'start_voice')}
              >
                <Mic className="w-4 h-4 text-green-400" />
              </button>
            ) : (
              <button
                onClick={handleSendMessage}
                className="shrink-0 p-1.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-lg transition-all flex items-center justify-center disabled:opacity-50 shadow-lg shadow-green-900/30"
                title={t(currentLanguage, 'send_message')}
                disabled={loading}
              >
                <Send className="w-4 h-4 text-white" />
              </button>
            )}
          </div>
        </div>
        <div className="text-xs text-center text-gray-500 mt-2">
          {t(currentLanguage, 'tip')} {t(currentLanguage, 'upload_image')} • {t(currentLanguage, 'ask_about_tasks')} • 🎤 {t(currentLanguage, 'voice_available')}
        </div>
      </div>
    </div>
  );
};

export default InputArea;
