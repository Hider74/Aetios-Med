export interface TopicNode {
  id: string;
  label: string;
  type?: string;
  confidence: number; // 0-1 scale
  lastReviewed: Date | null;
  timesReviewed: number;
  mastered: boolean;
  in_scope?: boolean; // NEW: for semester scoping
  resources: string[] | {
    teachmeanatomy?: string;
    teachmesurgery?: string;
    quesmed?: string;
    nice?: string;
    bnf?: string;
    zerotofinals?: string;
  };
  notes: string;
  subtopics?: string[];
  parentTopics?: string[];
  anki_cards_count?: number;
  notes_count?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface KnowledgeGraph {
  nodes: TopicNode[];
  edges: GraphEdge[];
  metadata: {
    lastUpdated: Date;
    totalTopics: number;
    averageConfidence: number;
    masteredTopics: number;
  };
}

export interface GraphLayout {
  name: 'cola' | 'dagre' | 'circle' | 'grid' | 'random';
  animate: boolean;
  fit: boolean;
}

export interface GraphFilter {
  minConfidence?: number;
  maxConfidence?: number;
  showMastered?: boolean;
  showUnreviewed?: boolean;
  searchQuery?: string;
}

export interface GraphStats {
  totalNodes: number;
  totalEdges: number;
  averageConfidence: number;
  masteredCount: number;
  lowConfidenceCount: number;
  unreviewedCount: number;
}

// Semester Scope Types
export interface SemesterScope {
  id: number;
  name: string;
  year?: number;
  semester_number?: number;
  exam_date?: string;
  topic_ids: string[];
  source_filename?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface SemesterTopicMatch {
  topic_id: string;
  topic_label: string;
  match_score: number;
}

export interface SemesterUploadResponse {
  matched_topics: SemesterTopicMatch[];
  scope_id?: number;
  source_filename: string;
}
