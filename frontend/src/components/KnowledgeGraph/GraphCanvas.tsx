import React, { useEffect, useRef } from 'react';
import cytoscape, { Core, EventObject } from 'cytoscape';
// @ts-ignore - No type definitions available
import cola from 'cytoscape-cola';
// @ts-ignore - No type definitions available
import dagre from 'cytoscape-dagre';
import { useGraph } from '../../hooks/useGraph';
import { graphStyles, getConfidenceColor, getNodeSize } from './styles';
import { LoadingSpinner } from '../common/LoadingSpinner';

// Register layouts
cytoscape.use(cola);
cytoscape.use(dagre);

interface GraphCanvasProps {
  onNodeSelect?: (nodeId: string) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ onNodeSelect }) => {
  const { graph, loading, filteredNodes, layout, setSelectedNode } = useGraph();
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !graph) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: graphStyles,
      wheelSensitivity: 0.2,
      minZoom: 0.1,
      maxZoom: 3,
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, []);

  // Update graph data
  useEffect(() => {
    if (!cyRef.current || !graph) return;

    const cy = cyRef.current;
    
    // Clear existing elements
    cy.elements().remove();

    // Get connection counts for node sizing
    const connectionCounts = new Map<string, number>();
    graph.edges.forEach(edge => {
      connectionCounts.set(edge.source, (connectionCounts.get(edge.source) || 0) + 1);
      connectionCounts.set(edge.target, (connectionCounts.get(edge.target) || 0) + 1);
    });

    // Add nodes
    const nodeElements = filteredNodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        color: getConfidenceColor(node.confidence),
        size: getNodeSize(connectionCounts.get(node.id) || 0),
        mastered: node.mastered,
        confidence: node.confidence,
      },
    }));

    // Add edges (only for visible nodes)
    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));
    const edgeElements = graph.edges
      .filter(edge => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map(edge => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          relationship: edge.relationship,
        },
      }));

    cy.add([...nodeElements, ...edgeElements]);

    // Apply layout
    const layoutOptions = {
      name: layout.name,
      animate: layout.animate,
      fit: layout.fit,
      padding: 50,
      ...(layout.name === 'cola' && {
        nodeSpacing: 50,
        edgeLength: 100,
        randomize: false,
      }),
      ...(layout.name === 'dagre' && {
        rankDir: 'TB',
        nodeSep: 50,
        rankSep: 100,
      }),
    };

    cy.layout(layoutOptions).run();

    // Node click handler
    cy.on('tap', 'node', (event: EventObject) => {
      const node = event.target;
      const nodeData = filteredNodes.find(n => n.id === node.id());
      if (nodeData) {
        setSelectedNode(nodeData);
        if (onNodeSelect) {
          onNodeSelect(node.id());
        }
      }
    });

    // Background click (deselect)
    cy.on('tap', (event: EventObject) => {
      if (event.target === cy) {
        setSelectedNode(null);
      }
    });

  }, [graph, filteredNodes, layout, setSelectedNode, onNodeSelect]);

  // Handle layout changes
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;
    const layoutOptions = {
      name: layout.name,
      animate: layout.animate,
      fit: layout.fit,
      padding: 50,
    };

    cy.layout(layoutOptions).run();
  }, [layout]);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading knowledge graph..." />
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full bg-gray-50 dark:bg-gray-900"
      style={{ minHeight: '500px' }}
    />
  );
};
