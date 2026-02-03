import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ipc } from '../services/ipc';

interface AppSettings {
  // Appearance
  theme: 'light' | 'dark' | 'auto';
  sidebarCollapsed: boolean;
  fontSize: 'small' | 'medium' | 'large';
  
  // Study
  dailyGoalMinutes: number;
  reminderEnabled: boolean;
  reminderTime: string;
  studyMode: 'casual' | 'focused' | 'exam_prep';
  
  // Streak tracking
  currentStreak: number;
  longestStreak: number;
  lastStudyDate: string | null; // ISO date string
  
  // Daily goals
  dailyGoalTopics: number;
  dailyGoalQuizzes: number;
  topicsReviewedToday: number;
  quizzesCompletedToday: number;
  lastGoalResetDate: string | null; // ISO date string
  
  // Model
  modelName: string;
  modelPath: string;
  useGPU: boolean;
  
  // Resources
  resourceFolders: string[];
  autoScanResources: boolean;
  
  // Graph
  defaultGraphLayout: 'cola' | 'dagre' | 'circle' | 'grid';
  showConfidenceColors: boolean;
  animateTransitions: boolean;
  
  // Privacy
  telemetryEnabled: boolean;
  crashReportsEnabled: boolean;
  
  // Advanced
  apiPort: number;
  maxConcurrentRequests: number;
  cacheSize: number;
}

interface SettingsState extends AppSettings {
  loading: boolean;
  error: string | null;
  
  // Actions
  loadSettings: () => Promise<void>;
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => Promise<void>;
  resetSettings: () => void;
  addResourceFolder: (path: string) => void;
  removeResourceFolder: (path: string) => void;
  clearError: () => void;
  incrementStreak: () => void;
  incrementTopicsReviewed: () => void;
  incrementQuizzesCompleted: () => void;
  checkAndResetDailyGoals: () => void;
}

const defaultSettings: AppSettings = {
  theme: 'dark',
  sidebarCollapsed: false,
  fontSize: 'medium',
  dailyGoalMinutes: 120,
  reminderEnabled: false,
  reminderTime: '09:00',
  studyMode: 'casual',
  currentStreak: 0,
  longestStreak: 0,
  lastStudyDate: null,
  dailyGoalTopics: 5,
  dailyGoalQuizzes: 3,
  topicsReviewedToday: 0,
  quizzesCompletedToday: 0,
  lastGoalResetDate: null,
  modelName: 'OpenBioLLM-8B',
  modelPath: '',
  useGPU: true,
  resourceFolders: [],
  autoScanResources: true,
  defaultGraphLayout: 'cola',
  showConfidenceColors: true,
  animateTransitions: true,
  telemetryEnabled: false,
  crashReportsEnabled: true,
  apiPort: 8741,
  maxConcurrentRequests: 5,
  cacheSize: 100,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...defaultSettings,
      loading: false,
      error: null,

      loadSettings: async () => {
        set({ loading: true, error: null });
        try {
          const settings = await ipc.getSettings();
          set({ ...settings, loading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to load settings',
            loading: false 
          });
        }
      },

      updateSetting: async (key, value) => {
        try {
          await ipc.saveSetting(key, value);
          set({ [key]: value } as any);
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to save setting' });
        }
      },

      resetSettings: () => {
        set(defaultSettings);
        Object.entries(defaultSettings).forEach(([key, value]) => {
          ipc.saveSetting(key, value).catch(console.error);
        });
      },

      addResourceFolder: (path) => {
        const folders = get().resourceFolders;
        if (!folders.includes(path)) {
          const newFolders = [...folders, path];
          set({ resourceFolders: newFolders });
          ipc.saveSetting('resourceFolders', newFolders);
        }
      },

      removeResourceFolder: (path) => {
        const newFolders = get().resourceFolders.filter(f => f !== path);
        set({ resourceFolders: newFolders });
        ipc.saveSetting('resourceFolders', newFolders);
      },

      clearError: () => {
        set({ error: null });
      },

      incrementStreak: () => {
        const today = new Date().toISOString().split('T')[0];
        const { lastStudyDate, currentStreak, longestStreak } = get();
        
        if (lastStudyDate === today) {
          // Already studied today
          return;
        }
        
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        
        let newStreak: number;
        if (lastStudyDate === yesterdayStr) {
          // Continuing streak
          newStreak = currentStreak + 1;
        } else {
          // Starting new streak
          newStreak = 1;
        }
        
        const newLongestStreak = Math.max(longestStreak, newStreak);
        
        set({ 
          currentStreak: newStreak,
          longestStreak: newLongestStreak,
          lastStudyDate: today 
        });
        
        // Persist to IPC
        ipc.saveSetting('currentStreak', newStreak).catch(console.error);
        ipc.saveSetting('longestStreak', newLongestStreak).catch(console.error);
        ipc.saveSetting('lastStudyDate', today).catch(console.error);
      },

      checkAndResetDailyGoals: () => {
        const today = new Date().toISOString().split('T')[0];
        const { lastGoalResetDate } = get();
        
        if (lastGoalResetDate !== today) {
          // Reset daily counters
          set({
            topicsReviewedToday: 0,
            quizzesCompletedToday: 0,
            lastGoalResetDate: today,
          });
          
          ipc.saveSetting('topicsReviewedToday', 0).catch(console.error);
          ipc.saveSetting('quizzesCompletedToday', 0).catch(console.error);
          ipc.saveSetting('lastGoalResetDate', today).catch(console.error);
        }
      },

      incrementTopicsReviewed: () => {
        get().checkAndResetDailyGoals();
        const newCount = get().topicsReviewedToday + 1;
        set({ topicsReviewedToday: newCount });
        ipc.saveSetting('topicsReviewedToday', newCount).catch(console.error);
        get().incrementStreak();
      },

      incrementQuizzesCompleted: () => {
        get().checkAndResetDailyGoals();
        const newCount = get().quizzesCompletedToday + 1;
        set({ quizzesCompletedToday: newCount });
        ipc.saveSetting('quizzesCompletedToday', newCount).catch(console.error);
        get().incrementStreak();
      },
    }),
    {
      name: 'settings-store',
    }
  )
);
