export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  relatedTopics?: string[];
  quiz?: QuizData;
  resources?: ResourceReference[];
}

export interface QuizData {
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  topic: string;
  answered?: boolean;
  userAnswer?: number;
  isCorrect?: boolean;
}

export interface ResourceReference {
  type: 'pdf' | 'video' | 'article' | 'website';
  title: string;
  url: string;
  page?: number;
  timestamp?: string;
}

export interface ChatResponse {
  message: string;
  confidence: number;
  sources: ResourceReference[];
  suggestedTopics?: string[];
  quiz?: QuizData;
  graphUpdate?: {
    updatedNodes: string[];
    newConfidences: Record<string, number>;
  };
}

export interface ChatContext {
  currentTopic?: string;
  recentTopics: string[];
  studyMode: 'casual' | 'focused' | 'exam_prep';
  difficultyPreference: 'easy' | 'medium' | 'hard';
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  startTime: Date;
  lastActivity: Date;
  topicsCovered: string[];
}
