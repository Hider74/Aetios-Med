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
}

const defaultSettings: AppSettings = {
  theme: 'dark',
  sidebarCollapsed: false,
  fontSize: 'medium',
  dailyGoalMinutes: 120,
  reminderEnabled: false,
  reminderTime: '09:00',
  studyMode: 'casual',
  modelName: 'BioMistral-7B',
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
    }),
    {
      name: 'settings-store',
    }
  )
);
