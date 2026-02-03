import React, { useState, useRef } from 'react';
import { Sidebar } from './components/common/Sidebar';
import { TopBar } from './components/common/TopBar';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { UserGuidePanel } from './components/common/UserGuidePanel';
import { Dashboard } from './components/Dashboard/Dashboard';
import { GraphCanvas } from './components/KnowledgeGraph/GraphCanvas';
import { GraphControls } from './components/KnowledgeGraph/GraphControls';
import { NodeDetail } from './components/KnowledgeGraph/NodeDetail';
import { ChatInterface } from './components/Chat/ChatInterface';
import { PlanGenerator } from './components/StudyPlan/PlanGenerator';
import { CalendarView } from './components/StudyPlan/CalendarView';
import { WebViewPanel } from './components/ResourceViewer/WebViewPanel';
import { ModelDownload } from './components/Setup/ModelDownload';
import { HuggingFaceAuth } from './components/Setup/HuggingFaceAuth';
import { FolderConfig } from './components/Setup/FolderConfig';
import { useGraph } from './hooks/useGraph';
import { useSettingsStore } from './stores/settingsStore';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { HelpCircle } from 'lucide-react';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [chatInitialMessage, setChatInitialMessage] = useState<string | null>(null);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const { selectedNode, setSelectedNode } = useGraph();
  const { theme } = useSettingsStore();
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  const handleQuickStudy = (topic: string) => {
    setChatInitialMessage(`Let's study ${topic}. Start with a quick overview.`);
    setCurrentPage('chat');
  };

  // Helper function to focus chat input
  const focusChatInput = () => {
    const chatInput = document.querySelector('textarea[placeholder*="Ask a question"]') as HTMLTextAreaElement;
    if (chatInput) {
      chatInput.focus();
    }
  };

  // Setup keyboard shortcuts
  useKeyboardShortcuts({
    onNavigateDashboard: () => setCurrentPage('dashboard'),
    onNavigateGraph: () => setCurrentPage('graph'),
    onNavigateChat: () => setCurrentPage('chat'),
    onNavigateStudyPlan: () => setCurrentPage('study'),
    onFocusChatInput: () => {
      // Focus chat input if on chat page
      if (currentPage === 'chat') {
        focusChatInput();
      } else {
        // Navigate to chat page and focus input
        setCurrentPage('chat');
        setTimeout(focusChatInput, 100);
      }
    },
    onCloseModal: () => {
      // Close node detail panel if open
      if (selectedNode) {
        setSelectedNode(null);
      }
    },
  });

  const getPageTitle = () => {
    switch (currentPage) {
      case 'dashboard': return 'Dashboard';
      case 'graph': return 'Knowledge Graph';
      case 'chat': return 'AI Tutor';
      case 'study': return 'Study Plan';
      case 'resources': return 'Resources';
      case 'settings': return 'Settings';
      default: return 'Aetios-Med';
    }
  };

  const getPageSubtitle = () => {
    switch (currentPage) {
      case 'dashboard': return 'Your study progress overview';
      case 'graph': return 'Visualize your knowledge connections';
      case 'chat': return 'Learn with AI assistance';
      case 'study': return 'Plan and track your study sessions';
      case 'resources': return 'Browse medical resources';
      case 'settings': return 'Configure your preferences';
      default: return '';
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <ErrorBoundary>
            <Dashboard onNavigate={setCurrentPage} onQuickStudy={handleQuickStudy} />
          </ErrorBoundary>
        );
      
      case 'graph':
        return (
          <ErrorBoundary>
            <div className="relative h-full">
              <GraphCanvas 
                onNodeSelect={(id) => console.log('Selected:', id)}
                onNavigateToChat={(message) => {
                  setChatInitialMessage(message);
                  setCurrentPage('chat');
                }}
              />
              <GraphControls />
              {selectedNode && (
                <NodeDetail 
                  onClose={() => setSelectedNode(null)}
                  onStartStudy={(id) => {
                    setCurrentPage('chat');
                    console.log('Start study:', id);
                  }}
                />
              )}
            </div>
          </ErrorBoundary>
        );
      
      case 'chat':
        return (
          <ErrorBoundary>
            <ChatInterface initialMessage={chatInitialMessage} onMessageSent={() => setChatInitialMessage(null)} />
          </ErrorBoundary>
        );
      
      case 'study':
        return (
          <ErrorBoundary>
            <div className="p-6 space-y-6 max-w-7xl mx-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PlanGenerator />
                <CalendarView />
              </div>
            </div>
          </ErrorBoundary>
        );
      
      case 'resources':
        return (
          <ErrorBoundary>
            <WebViewPanel />
          </ErrorBoundary>
        );
      
      case 'settings':
        return (
          <ErrorBoundary>
            <div className="p-6 space-y-6 max-w-4xl mx-auto">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Setup</h2>
                <div className="space-y-8">
                  <ModelDownload />
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-8">
                    <HuggingFaceAuth />
                  </div>
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-8">
                    <FolderConfig />
                  </div>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        );
      
      default:
        return (
          <ErrorBoundary>
            <Dashboard />
          </ErrorBoundary>
        );
    }
  };

  return (
    <div className={`flex h-screen ${theme === 'dark' ? 'dark' : ''}`}>
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={getPageTitle()} subtitle={getPageSubtitle()} />
        
        <main className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900">
          {renderPage()}
        </main>
      </div>

      {/* Floating help button */}
      <button
        onClick={() => setIsGuideOpen(true)}
        className="fixed bottom-6 right-6 z-50 p-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-110 focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2"
        aria-label="Open user guide"
        title="User Guide"
      >
        <HelpCircle className="w-6 h-6" />
      </button>

      {/* User guide panel */}
      <UserGuidePanel isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />
    </div>
  );
}

export default App;
