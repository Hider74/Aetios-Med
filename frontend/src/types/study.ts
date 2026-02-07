export interface Exam {
  id: string;
  name: string;
  date: Date;
  topics: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  completed: boolean;
  score?: number;
  notes?: string;
}

export interface StudySession {
  id: string;
  topicId: string;
  startTime: Date;
  endTime?: Date;
  duration: number; // minutes
  confidenceBefore: number;
  confidenceAfter?: number;
  quizzesTaken: number;
  quizzesCorrect: number;
  notes: string;
}

export interface StudyPlan {
  id: string;
  name: string;
  examId: string;
  startDate: Date;
  endDate: Date;
  dailyGoalMinutes: number;
  tasks: StudyTask[];
  progress: number; // 0-100
  generatedAt: Date;
}

export interface StudyTask {
  id: string;
  topicId: string;
  topicName: string;
  scheduledDate: Date;
  estimatedDuration: number; // minutes
  priority: number;
  completed: boolean;
  completedAt?: Date;
  confidenceGoal: number;
  actualConfidence?: number;
  type: 'review' | 'deep_study' | 'quiz' | 'practice';
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  source?: string;
}

export interface QuizSession {
  id: string;
  topicId: string;
  questions: QuizQuestion[];
  currentIndex: number;
  answers: (number | null)[];
  startTime: Date;
  endTime?: Date;
  score?: number;
}

export interface StudyPlanPreferences {
  dailyGoalMinutes?: number;
  studyStyle?: 'spaced' | 'intensive' | 'balanced';
  priorityTopics?: string[];
  avoidWeekends?: boolean;
  preferredTimes?: string[];
}

export interface Resource {
  id: string;
  type: 'pdf' | 'video' | 'article' | 'website' | 'anki' | 'note';
  title: string;
  content?: string;
  url?: string;
  filePath?: string;
  metadata?: Record<string, unknown>; // Changed from any to unknown for better type safety
  createdAt?: Date;
  updatedAt?: Date;
}

export interface DecayingTopic {
  topicId: string;
  topicName: string;
  currentConfidence: number;
  lastReviewed: Date;
  daysSinceReview: number;
  estimatedDecay: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  recommendedReviewDate: Date;
}

export interface StudyStats {
  totalStudyTime: number; // minutes
  topicsStudied: number;
  quizzesTaken: number;
  quizzesCorrect: number;
  averageAccuracy: number;
  currentStreak: number;
  longestStreak: number;
  lastStudySession?: Date;
}
