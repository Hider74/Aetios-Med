export interface TopicNode {
  id: string;
  label: string;
  confidence: number; // 0-1 scale
  lastReviewed: Date | null;
  timesReviewed: number;
  mastered: boolean;
  resources: string[];
  notes: string;
  subtopics?: string[];
  parentTopics?: string[];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: 'prerequisite' | 'related' | 'subtopic';
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
