import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, ChatSession, ChatContext } from '../types/chat';
import { api } from '../services/api';

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  context: ChatContext;
  isTyping: boolean;

  // Actions
  createSession: (title?: string) => void;
  switchSession: (sessionId: string) => void;
  sendMessage: (content: string) => Promise<void>;
  loadHistory: (sessionId?: string) => Promise<void>;
  clearMessages: () => void;
  setContext: (context: Partial<ChatContext>) => void;
  deleteSession: (sessionId: string) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      messages: [],
      loading: false,
      error: null,
      isTyping: false,
      context: {
        recentTopics: [],
        studyMode: 'casual',
        difficultyPreference: 'medium',
      },

      createSession: (title = 'New Chat') => {
        const newSession: ChatSession = {
          id: `session-${Date.now()}`,
          title,
          messages: [],
          startTime: new Date(),
          lastActivity: new Date(),
          topicsCovered: [],
        };
        set(state => ({
          sessions: [...state.sessions, newSession],
          currentSessionId: newSession.id,
          messages: [],
        }));
      },

      switchSession: (sessionId) => {
        const session = get().sessions.find(s => s.id === sessionId);
        if (session) {
          set({ 
            currentSessionId: sessionId,
            messages: session.messages 
          });
        }
      },

      sendMessage: async (content) => {
        const state = get();
        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          role: 'user',
          content,
          timestamp: new Date(),
        };

        // Add user message immediately
        set({ 
          messages: [...state.messages, userMessage],
          loading: true,
          isTyping: true,
          error: null 
        });

        try {
          const response = await api.sendMessage(content, state.context);
          
          const assistantMessage: ChatMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: response.message,
            timestamp: new Date(),
            relatedTopics: response.suggestedTopics,
            quiz: response.quiz,
            resources: response.sources,
          };

          const messages = [...state.messages, userMessage, assistantMessage];
          
          // Update session
          const sessions = state.sessions.map(session => {
            if (session.id === state.currentSessionId) {
              return {
                ...session,
                messages,
                lastActivity: new Date(),
                topicsCovered: [...new Set([
                  ...session.topicsCovered,
                  ...(response.suggestedTopics || [])
                ])],
              };
            }
            return session;
          });

          set({ 
            messages,
            sessions,
            loading: false,
            isTyping: false 
          });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to send message',
            loading: false,
            isTyping: false 
          });
        }
      },

      loadHistory: async (sessionId) => {
        set({ loading: true, error: null });
        try {
          const messages = await api.getChatHistory(sessionId);
          set({ messages, loading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to load history',
            loading: false 
          });
        }
      },

      clearMessages: () => {
        set({ messages: [] });
      },

      setContext: (context) => {
        set(state => ({ 
          context: { ...state.context, ...context } 
        }));
      },

      deleteSession: (sessionId) => {
        set(state => ({
          sessions: state.sessions.filter(s => s.id !== sessionId),
          currentSessionId: state.currentSessionId === sessionId 
            ? null 
            : state.currentSessionId,
        }));
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'chat-store',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        context: state.context,
      }),
    }
  )
);
