import axios, { AxiosInstance, AxiosError } from 'axios';
import type { KnowledgeGraph, TopicNode } from '../types/curriculum';
import type { ChatMessage, ChatResponse, ChatContext } from '../types/chat';
import type { Exam, StudyPlan, QuizQuestion, StudySession, StudyPlanPreferences, Resource, SAQQuestion, SAQResult } from '../types/study';

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
  async sendMessage(message: string, context?: ChatContext): Promise<ChatResponse> {
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
    }, {
      timeout: 300_000, // 5 minutes for LLM inference
    });
    
    // Basic runtime validation
    if (!response.data || typeof response.data.message !== 'string') {
      throw new Error('Invalid response from chat API');
    }
    
    return response.data;
  }

  async getChatHistory(sessionId?: string): Promise<ChatMessage[]> {
    const response = await this.client.get<ChatMessage[]>('/chat/history', {
      params: { sessionId },
    });
    return response.data;
  }

  // Study Plans
  async generateStudyPlan(examId: string, preferences: StudyPlanPreferences): Promise<StudyPlan> {
    const response = await this.client.post<StudyPlan>('/study/plan/generate', {
      examId,
      preferences,
    }, {
      timeout: 300_000, // 5 minutes for LLM-based plan generation
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
    const response = await this.client.get<Exam[]>('/study/exams');
    return response.data.map((exam: Exam) => ({
      ...exam,
      date: new Date(exam.date),
    }));
  }

  async createExam(exam: Partial<Exam>): Promise<Exam> {
    const response = await this.client.post<Exam>('/study/exam', exam);
    return {
      ...response.data,
      date: new Date(response.data.date),
    };
  }

  async updateExam(examId: string, updates: Partial<Exam>): Promise<Exam> {
    const response = await this.client.patch<Exam>(`/study/exam/${examId}`, updates);
    return {
      ...response.data,
      date: new Date(response.data.date),
    };
  }

  async deleteExam(examId: string): Promise<void> {
    await this.client.delete(`/study/exam/${examId}`);
  }

  // Quizzes
  async generateQuiz(topicIds: string[], count: number = 5, questionType: string = 'sba'): Promise<QuizQuestion[]> {
    const response = await this.client.post<{ questions: QuizQuestion[] }>('/quiz/generate', {
      topic_ids: topicIds,
      num_questions: count,
      difficulty: 'medium',
      question_type: questionType,
    }, {
      timeout: 300_000, // 5 minutes for LLM-based quiz generation
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

  async submitSAQAnswer(quizId: string, questionId: string, topicId: string, answer: string): Promise<SAQResult> {
    const response = await this.client.post<SAQResult>('/quiz/submit-saq', {
      quiz_id: quizId,
      question_id: questionId,
      topic_id: topicId,
      answer,
    }, {
      timeout: 300_000, // LLM marking can take time
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
  async searchResources(query: string): Promise<Resource[]> {
    const response = await this.client.get<Resource[]>('/resources/search', {
      params: { query },
    });
    return response.data;
  }

  async getResourceContent(resourceId: string): Promise<Resource> {
    const response = await this.client.get<Resource>(`/resources/${resourceId}`);
    return response.data;
  }

  // Semester Scope API
  async uploadSemesterPDF(
    file: File,
    name: string,
    year?: number,
    semester_number?: number,
    exam_date?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (year) formData.append('year', year.toString());
    if (semester_number) formData.append('semester_number', semester_number.toString());
    if (exam_date) formData.append('exam_date', exam_date);

    const response = await this.client.post('/semester/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async createSemesterScope(scopeData: {
    name: string;
    topic_ids: string[];
    year?: number;
    semester_number?: number;
    exam_date?: string;
    source_filename?: string;
  }): Promise<any> {
    const response = await this.client.post('/semester/create', scopeData);
    return response.data;
  }

  async uploadAndCreateSemesterScope(
    file: File,
    name: string,
    year?: number,
    semester_number?: number,
    exam_date?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (year) formData.append('year', year.toString());
    if (semester_number) formData.append('semester_number', semester_number.toString());
    if (exam_date) formData.append('exam_date', exam_date);

    const response = await this.client.post('/semester/upload-and-create', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async getSemesterScopes(): Promise<any> {
    const response = await this.client.get('/semester/scopes');
    return response.data;
  }

  async getActiveSemesterScope(): Promise<any> {
    const response = await this.client.get('/semester/active');
    return response.data;
  }

  async activateSemesterScope(scopeId: number): Promise<any> {
    const response = await this.client.put(`/semester/${scopeId}/activate`);
    return response.data;
  }

  async deactivateSemesterScope(): Promise<any> {
    const response = await this.client.put('/semester/deactivate');
    return response.data;
  }

  async updateSemesterScopeTopics(scopeId: number, topic_ids: string[]): Promise<any> {
    const response = await this.client.put(`/semester/${scopeId}/topics`, { topic_ids });
    return response.data;
  }

  async deleteSemesterScope(scopeId: number): Promise<any> {
    const response = await this.client.delete(`/semester/${scopeId}`);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
