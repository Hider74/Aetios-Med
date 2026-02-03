// Type exports
export type { TopicNode, GraphEdge, KnowledgeGraph, GraphLayout, GraphFilter, GraphStats } from './types/curriculum';
export type { ChatMessage, ChatResponse, QuizData, ChatSession, ChatContext } from './types/chat';
export type { Exam, StudyPlan, StudyTask, QuizQuestion, StudySession, DecayingTopic, StudyStats } from './types/study';

// Service exports
export { api } from './services/api';
export { ipc } from './services/ipc';

// Store exports
export { useGraphStore } from './stores/graphStore';
export { useChatStore } from './stores/chatStore';
export { useSettingsStore } from './stores/settingsStore';

// Hook exports
export { useGraph } from './hooks/useGraph';
export { useChat } from './hooks/useChat';
export { useStudySession } from './hooks/useStudySession';
export { useModelStatus } from './hooks/useModelStatus';

// Component exports - Common
export { Sidebar } from './components/common/Sidebar';
export { TopBar } from './components/common/TopBar';
export { LoadingSpinner } from './components/common/LoadingSpinner';
export { UserGuidePanel } from './components/common/UserGuidePanel';

// Component exports - Dashboard
export { Dashboard } from './components/Dashboard/Dashboard';
export { ConfidenceOverview } from './components/Dashboard/ConfidenceOverview';
export { UpcomingExams } from './components/Dashboard/UpcomingExams';
export { DecayingTopics } from './components/Dashboard/DecayingTopics';

// Component exports - Knowledge Graph
export { GraphCanvas } from './components/KnowledgeGraph/GraphCanvas';
export { GraphControls } from './components/KnowledgeGraph/GraphControls';
export { NodeDetail } from './components/KnowledgeGraph/NodeDetail';

// Component exports - Chat
export { ChatInterface } from './components/Chat/ChatInterface';
export { MessageBubble } from './components/Chat/MessageBubble';
export { QuizCard } from './components/Chat/QuizCard';

// Component exports - Study Plan
export { PlanGenerator } from './components/StudyPlan/PlanGenerator';
export { CalendarView } from './components/StudyPlan/CalendarView';
export { ExportICS } from './components/StudyPlan/ExportICS';

// Component exports - Setup
export { ModelDownload } from './components/Setup/ModelDownload';
export { HuggingFaceAuth } from './components/Setup/HuggingFaceAuth';
export { FolderConfig } from './components/Setup/FolderConfig';

// Component exports - Resource Viewer
export { WebViewPanel } from './components/ResourceViewer/WebViewPanel';
