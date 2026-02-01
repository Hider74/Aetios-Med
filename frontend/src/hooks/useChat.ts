import { useEffect, useCallback } from 'react';
import { useChatStore } from '../stores/chatStore';
import type { ChatMessage } from '../types/chat';

export const useChat = () => {
  const {
    sessions,
    currentSessionId,
    messages,
    loading,
    error,
    context,
    isTyping,
    createSession,
    switchSession,
    sendMessage,
    loadHistory,
    clearMessages,
    setContext,
    deleteSession,
    clearError,
  } = useChatStore();

  // Auto-create session if none exists
  useEffect(() => {
    if (sessions.length === 0) {
      createSession('Welcome Chat');
    }
  }, []);

  // Get current session
  const currentSession = sessions.find(s => s.id === currentSessionId);

  // Send message with automatic context update
  const handleSendMessage = useCallback(async (content: string) => {
    if (!currentSessionId) {
      createSession();
    }
    await sendMessage(content);
  }, [currentSessionId, sendMessage, createSession]);

  // Get messages for current session
  const getCurrentMessages = useCallback((): ChatMessage[] => {
    if (!currentSession) return [];
    return messages;
  }, [currentSession, messages]);

  // Get quiz from latest message
  const getLatestQuiz = useCallback(() => {
    const messagesWithQuiz = messages
      .filter(m => m.quiz)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    return messagesWithQuiz.length > 0 ? messagesWithQuiz[0].quiz : null;
  }, [messages]);

  // Answer quiz question
  const answerQuiz = useCallback((answer: number) => {
    const quiz = getLatestQuiz();
    if (!quiz) return;

    const isCorrect = answer === quiz.correctAnswer;
    
    // Update the quiz in the message
    const updatedMessages = messages.map(m => {
      if (m.quiz && m.quiz === quiz) {
        return {
          ...m,
          quiz: {
            ...m.quiz,
            answered: true,
            userAnswer: answer,
            isCorrect,
          },
        };
      }
      return m;
    });

    // Note: You'd need to add this to the store
    // For now, we'll send a follow-up message
    const feedback = isCorrect 
      ? `Correct! ${quiz.explanation}`
      : `Not quite. The correct answer was option ${quiz.correctAnswer + 1}. ${quiz.explanation}`;
    
    handleSendMessage(`I answered option ${answer + 1} for the quiz question.`);
  }, [messages, getLatestQuiz, handleSendMessage]);

  // Get topics covered in current session
  const getTopicsCovered = useCallback(() => {
    if (!currentSession) return [];
    return currentSession.topicsCovered;
  }, [currentSession]);

  // Create new session with optional title
  const startNewSession = useCallback((title?: string) => {
    createSession(title || `Chat ${sessions.length + 1}`);
  }, [createSession, sessions.length]);

  return {
    sessions,
    currentSession,
    messages: getCurrentMessages(),
    loading,
    error,
    context,
    isTyping,
    latestQuiz: getLatestQuiz(),
    topicsCovered: getTopicsCovered(),
    
    // Actions
    sendMessage: handleSendMessage,
    createSession: startNewSession,
    switchSession,
    loadHistory,
    clearMessages,
    setContext,
    deleteSession,
    clearError,
    answerQuiz,
  };
};
