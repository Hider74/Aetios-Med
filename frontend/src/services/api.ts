import axios, { AxiosInstance, AxiosError } from 'axios';
import type { KnowledgeGraph, TopicNode } from '../types/curriculum';
import type { ChatMessage, ChatResponse } from '../types/chat';
import type { Exam, StudyPlan, QuizQuestion, StudySession } from '../types/study';

const BASE_URL = 'http://localhost:8741/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.message);
        if (error.response) {
          console.error('Response:', error.response.data);
        }
        throw error;
      }
    );
  }

  // Health Check
  async checkHealth(): Promise<{ status: string; services: Record<string, boolean> }> {
    try {
      const response = await this.client.get('/system/health');
      return response.data;
    } catch (error) {
      return { status: 'error', services: {} };
    }
  }

  // Knowledge Graph
  async getGraph(): Promise<KnowledgeGraph> {
    const response = await this.client.get<KnowledgeGraph>('/graph');
    return response.data;
  }

  async updateNodeConfidence(nodeId: string, confidence: number): Promise<TopicNode> {
    const response = await this.client.patch<TopicNode>(`/graph/nodes/${nodeId}`, {
      confidence,
      lastReviewed: new Date().toISOString(),
    });
    return response.data;
  }

  async addNode(node: Partial<TopicNode>): Promise<TopicNode> {
    const response = await this.client.post<TopicNode>('/graph/nodes', node);
    return response.data;
  }

  async deleteNode(nodeId: string): Promise<void> {
    await this.client.delete(`/graph/nodes/${nodeId}`);
  }

  // Chat
  async sendMessage(message: string, context?: any): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat/message', {
      messages: [
        {
          role: 'user',
          content: message,
        },
      ],
      temperature: 0.7,
      max_tokens: 2048,
      session_id: 'default',
    });
    return response.data;
  }

  async getChatHistory(sessionId?: string): Promise<ChatMessage[]> {
    const response = await this.client.get<ChatMessage[]>('/chat/history', {
      params: { sessionId },
    });
    return response.data;
  }

  // Study Plans
  async generateStudyPlan(examId: string, preferences: any): Promise<StudyPlan> {
    const response = await this.client.post<StudyPlan>('/study/plan/generate', {
      examId,
      preferences,
    });
    return response.data;
  }

  async getStudyPlans(): Promise<StudyPlan[]> {
    const response = await this.client.get<StudyPlan[]>('/study/plans');
    return response.data;
  }

  async updateStudyTask(taskId: string, completed: boolean): Promise<void> {
    await this.client.patch(`/study/tasks/${taskId}`, { completed });
  }

  // Exams
  async getExams(): Promise<Exam[]> {
    const response = await this.client.get<any[]>('/study/exams');
    return response.data.map((exam: any) => ({
      ...exam,
      date: new Date(exam.date),
    }));
  }

  async createExam(exam: Partial<Exam>): Promise<Exam> {
    const response = await this.client.post<any>('/study/exam', exam);
    return {
      ...response.data,
      date: new Date(response.data.date),
    };
  }

  async updateExam(examId: string, updates: Partial<Exam>): Promise<Exam> {
    const response = await this.client.patch<any>(`/study/exam/${examId}`, updates);
    return {
      ...response.data,
      date: new Date(response.data.date),
    };
  }

  async deleteExam(examId: string): Promise<void> {
    await this.client.delete(`/study/exam/${examId}`);
  }

  // Quizzes
  async generateQuiz(topicIds: string[], count: number = 5): Promise<QuizQuestion[]> {
    const response = await this.client.post<any>('/quiz/generate', {
      topic_ids: topicIds,
      num_questions: count,
      difficulty: 'medium',
    });
    return response.data.questions || [];
  }

  async submitQuizAnswer(questionId: string, answer: number): Promise<{ correct: boolean; explanation: string }> {
    const response = await this.client.post(`/quiz/answer`, {
      questionId,
      answer,
    });
    return response.data;
  }

  // Study Sessions
  async startStudySession(topicId: string): Promise<StudySession> {
    const response = await this.client.post<StudySession>('/study/sessions', {
      topicId,
      startTime: new Date().toISOString(),
    });
    return response.data;
  }

  async endStudySession(sessionId: string, data: Partial<StudySession>): Promise<StudySession> {
    const response = await this.client.patch<StudySession>(`/study/sessions/${sessionId}`, {
      ...data,
      endTime: new Date().toISOString(),
    });
    return response.data;
  }

  // Model Status
  async getModelStatus(): Promise<{ loaded: boolean; model: string; progress?: number }> {
    const response = await this.client.get('/system/model-status');
    return response.data;
  }

  async downloadModel(modelName: string): Promise<void> {
    await this.client.post('/model/download', { modelName });
  }

  // Resources
  async searchResources(query: string): Promise<any[]> {
    const response = await this.client.get('/resources/search', {
      params: { query },
    });
    return response.data;
  }

  async getResourceContent(resourceId: string): Promise<any> {
    const response = await this.client.get(`/resources/${resourceId}`);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
