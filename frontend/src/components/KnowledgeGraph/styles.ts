// @ts-ignore - Cytoscape type issue with Stylesheet
import type { Stylesheet as CytoscapeStylesheet } from 'cytoscape';

// @ts-ignore
export const graphStyles: CytoscapeStylesheet[] = [
  // Node styles
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      'label': 'data(label)',
      'color': '#ffffff',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '12px',
      'font-weight': 'bold',
      'text-outline-width': 2,
      'text-outline-color': '#000000',
      'width': 'data(size)',
      'height': 'data(size)',
      'border-width': 2,
      'border-color': '#ffffff',
      'overlay-padding': '6px',
    },
  },
  // Mastered nodes
  {
    selector: 'node[mastered = true]',
    style: {
      'border-color': '#ffd700',
      'border-width': 3,
    },
  },
  // Selected node
  {
    selector: 'node:selected',
    style: {
      'border-color': '#60a5fa',
      'border-width': 4,
      'overlay-opacity': 0.2,
      'overlay-color': '#60a5fa',
    },
  },
  // Edge styles
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#4b5563',
      'target-arrow-color': '#4b5563',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 1,
    },
  },
  // Prerequisite edges (stronger connection)
  {
    selector: 'edge[relationship = "prerequisite"]',
    style: {
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
      'width': 3,
    },
  },
  // Related edges
  {
    selector: 'edge[relationship = "related"]',
    style: {
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'line-style': 'dashed',
    },
  },
  // Subtopic edges
  {
    selector: 'edge[relationship = "subtopic"]',
    style: {
      'line-color': '#10b981',
      'target-arrow-color': '#10b981',
    },
  },
  // Selected edge
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#60a5fa',
      'target-arrow-color': '#60a5fa',
      'width': 4,
    },
  },
];

// Confidence-based color mapping
export const getConfidenceColor = (confidence: number): string => {
  if (confidence <= 0.3) return '#ef4444'; // Red - Low confidence
  if (confidence <= 0.6) return '#f59e0b'; // Amber - Medium confidence
  return '#10b981'; // Green - High confidence
};

// Node size based on importance (number of connections)
export const getNodeSize = (connectionCount: number): number => {
  const baseSize = 40;
  const sizeIncrement = Math.min(connectionCount * 5, 40);
  return baseSize + sizeIncrement;
};
