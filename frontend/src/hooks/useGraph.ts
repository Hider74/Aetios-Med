import { useEffect, useCallback } from 'react';
import { useGraphStore } from '../stores/graphStore';
import type { TopicNode, GraphFilter, GraphLayout } from '../types/curriculum';

export const useGraph = () => {
  const {
    graph,
    loading,
    error,
    selectedNode,
    filter,
    layout,
    searchQuery,
    curriculumKey,
    availableCurricula,
    viewMode,
    fetchGraph,
    fetchCurricula,
    setActiveCurriculum,
    setSelectedNode,
    updateNodeConfidence,
    addNode,
    deleteNode,
    setFilter,
    setLayout,
    setSearchQuery,
    setViewMode,
    clearError,
  } = useGraphStore();

  // Auto-fetch graph on mount
  useEffect(() => {
    if (!graph) {
      fetchGraph();
    }
  }, []);

  // Auto-fetch available curricula on mount
  useEffect(() => {
    if (availableCurricula.length === 0) {
      fetchCurricula();
    }
  }, [availableCurricula.length, fetchCurricula]);

  // Filter nodes based on current filter settings
  const getFilteredNodes = useCallback(() => {
    if (!graph) return [];
    
    let nodes = graph.nodes;

    // Apply confidence filter
    if (filter.minConfidence !== undefined) {
      nodes = nodes.filter(n => n.confidence >= filter.minConfidence!);
    }
    if (filter.maxConfidence !== undefined) {
      nodes = nodes.filter(n => n.confidence <= filter.maxConfidence!);
    }

    // Apply mastered filter
    if (filter.showMastered === false) {
      nodes = nodes.filter(n => !n.mastered);
    }

    // Apply unreviewed filter
    if (filter.showUnreviewed === false) {
      nodes = nodes.filter(n => n.lastReviewed !== null);
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      nodes = nodes.filter(n => 
        n.label.toLowerCase().includes(query) ||
        (n.notes || '').toLowerCase().includes(query)
      );
    }

    return nodes;
  }, [graph, filter, searchQuery]);

  // Get graph statistics
  const getStats = useCallback(() => {
    if (!graph) return null;

    const nodes = graph.nodes;
    const totalNodes = nodes.length;
    const totalEdges = graph.edges.length;
    const masteredCount = nodes.filter(n => n.mastered).length;
    const lowConfidenceCount = nodes.filter(n => n.confidence < 0.3).length;
    const unreviewedCount = nodes.filter(n => !n.lastReviewed).length;
    
    const avgConfidence = totalNodes > 0
      ? nodes.reduce((sum, n) => sum + n.confidence, 0) / totalNodes
      : 0;

    return {
      totalNodes,
      totalEdges,
      averageConfidence: avgConfidence,
      masteredCount,
      lowConfidenceCount,
      unreviewedCount,
    };
  }, [graph]);

  // Get nodes that need review (low confidence or decaying)
  const getNodesNeedingReview = useCallback(() => {
    if (!graph) return [];

    const now = new Date();
    const oneDayMs = 24 * 60 * 60 * 1000;

    return graph.nodes
      .filter(n => {
        // Low confidence
        if (n.confidence < 0.4) return true;
        
        // Not reviewed recently
        if (n.lastReviewed) {
          const daysSinceReview = (now.getTime() - n.lastReviewed.getTime()) / oneDayMs;
          // Needs review if confidence is dropping based on time
          const decayThreshold = n.confidence > 0.7 ? 7 : 3;
          if (daysSinceReview > decayThreshold) return true;
        }
        
        return false;
      })
      .sort((a, b) => a.confidence - b.confidence);
  }, [graph]);

  // Get related nodes (connected by edges)
  const getRelatedNodes = useCallback((nodeId: string): TopicNode[] => {
    if (!graph) return [];

    const relatedIds = new Set<string>();
    graph.edges.forEach(edge => {
      if (edge.source === nodeId) relatedIds.add(edge.target);
      if (edge.target === nodeId) relatedIds.add(edge.source);
    });

    return graph.nodes.filter(n => relatedIds.has(n.id));
  }, [graph]);

  const getDomainNodes = useCallback((domainId: string): TopicNode[] => {
    if (!graph) return [];

    const domainNodeIds = new Set<string>();
    graph.edges.forEach(edge => {
      if (edge.relationship === 'BELONGS_TO' && edge.target === domainId) {
        domainNodeIds.add(edge.source);
      }
    });

    return graph.nodes.filter(node => domainNodeIds.has(node.id));
  }, [graph]);

  const getDomainStats = useCallback((domainId: string) => {
    const domainNodes = getDomainNodes(domainId);
    const totalNodes = domainNodes.length;
    if (totalNodes === 0) {
      return {
        totalNodes: 0,
        averageConfidence: 0,
        masteredCount: 0,
        lowConfidenceCount: 0,
        unreviewedCount: 0,
        weakestTopics: [] as TopicNode[],
      };
    }

    const masteredCount = domainNodes.filter(node => node.mastered).length;
    const lowConfidenceCount = domainNodes.filter(node => node.confidence < 0.3).length;
    const unreviewedCount = domainNodes.filter(node => !node.lastReviewed).length;
    const averageConfidence = domainNodes.reduce((sum, node) => sum + node.confidence, 0) / totalNodes;
    const weakestTopics = [...domainNodes]
      .sort((a, b) => a.confidence - b.confidence)
      .slice(0, 8);

    return {
      totalNodes,
      averageConfidence,
      masteredCount,
      lowConfidenceCount,
      unreviewedCount,
      weakestTopics,
    };
  }, [getDomainNodes]);

  return {
    graph,
    loading,
    error,
    selectedNode,
    filter,
    layout,
    searchQuery,
    curriculumKey,
    availableCurricula,
    viewMode,
    
    // Actions
    fetchGraph,
    fetchCurricula,
    setActiveCurriculum,
    setSelectedNode,
    updateNodeConfidence,
    addNode,
    deleteNode,
    setFilter,
    setLayout,
    setSearchQuery,
    setViewMode,
    clearError,
    
    // Computed
    filteredNodes: getFilteredNodes(),
    stats: getStats(),
    nodesNeedingReview: getNodesNeedingReview(),
    getRelatedNodes,
    getDomainNodes,
    getDomainStats,
  };
};
