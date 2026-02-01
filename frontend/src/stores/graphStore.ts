import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { KnowledgeGraph, TopicNode, GraphEdge, GraphFilter, GraphLayout } from '../types/curriculum';
import { api } from '../services/api';

interface GraphState {
  graph: KnowledgeGraph | null;
  loading: boolean;
  error: string | null;
  selectedNode: TopicNode | null;
  filter: GraphFilter;
  layout: GraphLayout;
  searchQuery: string;
  
  // Actions
  fetchGraph: () => Promise<void>;
  setSelectedNode: (node: TopicNode | null) => void;
  updateNodeConfidence: (nodeId: string, confidence: number) => Promise<void>;
  addNode: (node: Partial<TopicNode>) => Promise<void>;
  deleteNode: (nodeId: string) => Promise<void>;
  setFilter: (filter: Partial<GraphFilter>) => void;
  setLayout: (layout: GraphLayout) => void;
  setSearchQuery: (query: string) => void;
  clearError: () => void;
}

export const useGraphStore = create<GraphState>()(
  persist(
    (set, get) => ({
      graph: null,
      loading: false,
      error: null,
      selectedNode: null,
      filter: {
        showMastered: true,
        showUnreviewed: true,
      },
      layout: {
        name: 'cola',
        animate: true,
        fit: true,
      },
      searchQuery: '',

      fetchGraph: async () => {
        set({ loading: true, error: null });
        try {
          const graph = await api.getGraph();
          set({ graph, loading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch graph',
            loading: false 
          });
        }
      },

      setSelectedNode: (node) => {
        set({ selectedNode: node });
      },

      updateNodeConfidence: async (nodeId, confidence) => {
        try {
          const updatedNode = await api.updateNodeConfidence(nodeId, confidence);
          const graph = get().graph;
          if (graph) {
            const nodes = graph.nodes.map(n => 
              n.id === nodeId ? updatedNode : n
            );
            set({ 
              graph: { ...graph, nodes },
              selectedNode: updatedNode 
            });
          }
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to update node' });
        }
      },

      addNode: async (node) => {
        try {
          const newNode = await api.addNode(node);
          const graph = get().graph;
          if (graph) {
            set({ 
              graph: { 
                ...graph, 
                nodes: [...graph.nodes, newNode] 
              } 
            });
          }
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to add node' });
        }
      },

      deleteNode: async (nodeId) => {
        try {
          await api.deleteNode(nodeId);
          const graph = get().graph;
          if (graph) {
            const nodes = graph.nodes.filter(n => n.id !== nodeId);
            const edges = graph.edges.filter(
              e => e.source !== nodeId && e.target !== nodeId
            );
            set({ 
              graph: { ...graph, nodes, edges },
              selectedNode: null 
            });
          }
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to delete node' });
        }
      },

      setFilter: (filter) => {
        set(state => ({ 
          filter: { ...state.filter, ...filter } 
        }));
      },

      setLayout: (layout) => {
        set({ layout });
      },

      setSearchQuery: (query) => {
        set({ searchQuery: query });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'graph-store',
      partialize: (state) => ({
        filter: state.filter,
        layout: state.layout,
      }),
    }
  )
);
