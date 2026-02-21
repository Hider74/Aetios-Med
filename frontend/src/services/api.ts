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
  async getGraph(curriculum?: string): Promise<KnowledgeGraph> {
    const response = await this.client.get<KnowledgeGraph>('/graph', {
      params: curriculum ? { curriculum } : undefined,
    });
    const graph = response.data;
    const normalizedNodes = (graph.nodes || []).map((node) => ({
      ...node,
      notes: node.notes ?? '',
      mastered: node.mastered ?? (node.confidence >= 0.8),
      timesReviewed: node.timesReviewed ?? 0,
      lastReviewed: node.lastReviewed ? new Date(node.lastReviewed) : null,
      resources: node.resources ?? [],
    }));

    const normalizedEdges = (graph.edges || []).map((edge) => ({
      ...edge,
      id: edge.id || `${edge.source}-${edge.target}-${edge.relationship || 'related'}`,
      relationship: edge.relationship || 'related',
      weight: edge.weight ?? 1,
    }));

    return {
      ...graph,
      nodes: normalizedNodes,
      edges: normalizedEdges,
    };
  }

  async getCurricula(): Promise<{ active: string | null; available: string[] }> {
    const response = await this.client.get<{ active: string; available: string[] }>('/graph/curricula');
    return response.data;
  }

  async setActiveCurriculum(curriculum: string): Promise<{ active: string }> {
    const response = await this.client.post<{ active: string }>('/graph/active-curriculum', {
      curriculum,
    });
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
    const response = await this.client.post('/chat/message', {
      messages: [
        {
          role: 'user',
          content: message,
        },
      ],
      temperature: 0.7,
      session_id: 'default',
    }, {
      timeout: 300_000, // 5 minutes for LLM inference
    });
    
    // Backend returns { message: { role, content }, finish_reason }
    // Frontend expects { message: string, ... }
    // Transform the response
    const backendResponse = response.data;
    if (!backendResponse || !backendResponse.message) {
      throw new Error('Invalid response from chat API');
    }
    
    // Extract content from message object if needed
    const messageContent = typeof backendResponse.message === 'string' 
      ? backendResponse.message 
      : backendResponse.message.content;
    
    return {
      message: messageContent,
      confidence: 0.9, // Default confidence
      sources: [],
      suggestedTopics: [],
    };
  }

  async streamMessage(
    message: string,
    context?: ChatContext,
    options?: {
      sessionId?: string;
      temperature?: number;
      onChunk?: (chunk: string) => void;
    }
  ): Promise<string> {
    const payload = {
      messages: [
        {
          role: 'user',
          content: message,
        },
      ],
      temperature: options?.temperature ?? 0.7,
      session_id: options?.sessionId ?? 'default',
    };

    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
      const text = await response.text();
      throw new Error(text || 'Failed to stream chat response');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let separatorIndex = buffer.indexOf('\n\n');

      while (separatorIndex !== -1) {
        const rawEvent = buffer.slice(0, separatorIndex).trim();
        buffer = buffer.slice(separatorIndex + 2);

        const lines = rawEvent.split('\n').filter((line) => line.startsWith('data:'));
        for (const line of lines) {
          const data = line.replace('data:', '').trim();
          if (data === '[DONE]') {
            return fullText;
          }

          try {
            const parsed = JSON.parse(data);
            const chunk = typeof parsed.chunk === 'string' ? parsed.chunk : '';
            if (chunk) {
              fullText += chunk;
              options?.onChunk?.(chunk);
            }
          } catch (error) {
            // Ignore malformed chunks
          }
        }

        separatorIndex = buffer.indexOf('\n\n');
      }
    }

    return fullText;
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
  async generateQuiz(
    topicIds: string[],
    count: number = 5,
    questionType: string = 'sba'
  ): Promise<{ quizId: string; questions: Array<QuizQuestion | SAQQuestion>; topicId: string; difficulty: string; questionType: string }> {
    const response = await this.client.post<{ quiz_id: string; questions: any[]; topic_id: string; difficulty: string }>('/quiz/generate', {
      topic_ids: topicIds,
      num_questions: count,
      difficulty: 'medium',
      question_type: questionType,
    }, {
      timeout: 300_000, // 5 minutes for LLM-based quiz generation
    });

    const rawQuestions = response.data.questions || [];
    const mappedQuestions: Array<QuizQuestion | SAQQuestion> = rawQuestions.map((q, idx) => {
      if (questionType === 'saq') {
        return q as SAQQuestion;
      }

      const optionsObj = q.options || {};
      const optionKeys = ['A', 'B', 'C', 'D'];
      const options = optionKeys.map((key) => optionsObj[key]).filter(Boolean);
      const correctLetter = (q.correct_answer || '').toUpperCase();
      const correctIndex = optionKeys.indexOf(correctLetter);

      return {
        id: q.id || `q${idx}`,
        question: q.question,
        options,
        correctAnswer: correctIndex >= 0 ? correctIndex : 0,
        explanation: q.explanation || '',
        topic: q.topic_id || response.data.topic_id,
        difficulty: q.difficulty || response.data.difficulty || 'medium',
        source: q.source,
      } as QuizQuestion;
    });

    return {
      quizId: response.data.quiz_id,
      questions: mappedQuestions,
      topicId: response.data.topic_id,
      difficulty: response.data.difficulty,
      questionType,
    };
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
    // Backend returns is_loaded, map to loaded for frontend
    return {
      loaded: response.data.is_loaded,
      model: response.data.model_path || '',
      progress: response.data.progress,
    };
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

  // Tool Access Methods - Direct API calls for all agent tools
  
  async getWeakTopics(threshold: number = 0.3): Promise<any> {
    const response = await this.client.get('/graph/weak-topics', {
      params: { threshold },
    });
    return response.data.topics;
  }

  async getDecayingTopics(days: number = 7): Promise<any> {
    const response = await this.client.get('/graph/decaying-topics', {
      params: { days },
    });
    return response.data.topics;
  }

  async getPrerequisites(topicId: string): Promise<any> {
    const response = await this.client.get(`/graph/prerequisites/${topicId}`);
    return response.data.prerequisites;
  }

  async getDependentTopics(topicId: string): Promise<any> {
    const response = await this.client.get(`/graph/dependents/${topicId}`);
    return response.data.dependents;
  }

  async getTopicDetails(topicId: string): Promise<any> {
    const response = await this.client.get(`/graph/topic/${topicId}`);
    return response.data;
  }

  async searchNotes(query: string, limit: number = 5): Promise<any> {
    const response = await this.client.get('/graph/search-notes', {
      params: { query, limit },
    });
    return response.data.notes;
  }

  async getAnkiStats(topicId?: string): Promise<any> {
    const response = await this.client.get('/ingest/anki/due', {
      params: topicId ? { topic_id: topicId } : {},
    });
    return response.data;
  }

  async getStudyHistory(topicId?: string, days?: number): Promise<any> {
    const response = await this.client.get('/study/sessions', {
      params: { topic_id: topicId, limit: days ? Math.ceil(days * 2) : 20 },
    });
    return response.data.sessions;
  }

  async updateTopicConfidence(topicId: string, confidence: number, notes?: string): Promise<any> {
    const response = await this.client.post('/graph/confidence', {
      topic_id: topicId,
      confidence,
      notes,
    });
    return response.data;
  }

  async getExamReadiness(examId: number): Promise<any> {
    const response = await this.client.get(`/study/readiness/${examId}`);
    return response.data;
  }

  async getCurriculumOverview(): Promise<any> {
    const response = await this.client.get('/graph/statistics');
    return response.data;
  }

  async logQuizResult(topicId: string, correct: boolean, question: string): Promise<any> {
    // This is handled by submitQuizAnswer, but adding explicit method
    const response = await this.client.post('/quiz/submit', {
      topic_id: topicId,
      correct,
      question,
    });
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
