import React from 'react';
import { 
  LayoutDashboard, 
  Network, 
  MessageSquare, 
  Calendar, 
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

const menuItems = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'graph', icon: Network, label: 'Knowledge Graph' },
  { id: 'chat', icon: MessageSquare, label: 'AI Tutor' },
  { id: 'study', icon: Calendar, label: 'Study Plan' },
  { id: 'resources', icon: BookOpen, label: 'Resources' },
  { id: 'settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const { sidebarCollapsed, updateSetting } = useSettingsStore();

  const toggleSidebar = () => {
    updateSetting('sidebarCollapsed', !sidebarCollapsed);
  };

  return (
    <aside
      className={`
        bg-gray-900 text-white transition-all duration-300 flex flex-col
        ${sidebarCollapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        <img 
          src="/aetios-logo.png" 
          alt="Aetios-Med" 
          className={sidebarCollapsed ? "h-8 w-8 object-contain" : "h-10 object-contain"}
        />
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                w-full flex items-center gap-3 px-4 py-3 transition-colors
                ${isActive 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }
              `}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <Icon size={20} />
              {!sidebarCollapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        {!sidebarCollapsed && (
          <div className="text-xs text-gray-500">
            <p>Version 0.1.0</p>
            <p className="mt-1">Offline-first Study Assistant</p>
          </div>
        )}
      </div>
    </aside>
  );
};
