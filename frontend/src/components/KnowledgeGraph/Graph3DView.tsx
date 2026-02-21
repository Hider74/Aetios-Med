import React, { useMemo, useRef, useEffect, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import SpriteText from 'three-spritetext';
import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import { useGraph } from '../../hooks/useGraph';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface Graph3DViewProps {
  onNodeSelect?: (nodeId: string) => void;
}

const domainPalette = ['#22d3ee', '#60a5fa', '#f59e0b', '#a78bfa', '#f472b6', '#34d399'];

const getConfidenceColor = (confidence: number): string => {
  if (confidence <= 0.3) return '#ef4444';
  if (confidence <= 0.6) return '#f59e0b';
  return '#10b981';
};

export const Graph3DView: React.FC<Graph3DViewProps> = ({ onNodeSelect }) => {
  const { graph, loading, filteredNodes, setSelectedNode } = useGraph();
  const fgRef = useRef<any>(null);
  const initializedRef = useRef(false);
  const lastClickRef = useRef<{ id: string; ts: number } | null>(null);
  const gridRef = useRef<any>(null);
  const lightRef = useRef<any>(null);
  const css2dRendererRef = useRef<any>(null);
  const labelObjectsRef = useRef<Map<string, CSS2DObject>>(new Map());

  const graphData = useMemo(() => {
    // Clean up old labels when graph changes
    labelObjectsRef.current.forEach((label) => {
      if (label.element) {
        label.element.remove();
      }
    });
    labelObjectsRef.current.clear();

    if (!graph) {
      return { nodes: [], links: [] };
    }

    const visibleNodeIds = new Set(filteredNodes.map((node) => node.id));
    const links = graph.edges
      .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map((edge) => ({
        ...edge,
        relationship: edge.relationship || 'related',
      }));

    const domainIds = new Set(
      filteredNodes.filter((node) => node.type === 'Domain').map((node) => node.id)
    );

    const domainColorMap = new Map<string, string>();
    filteredNodes
      .filter((node) => node.type === 'Domain')
      .forEach((node, index) => {
        domainColorMap.set(node.id, domainPalette[index % domainPalette.length]);
      });

    const belongsTo = new Map<string, string>();
    links.forEach((link) => {
      if (link.relationship === 'BELONGS_TO' && domainIds.has(link.target)) {
        belongsTo.set(link.source, link.target);
      }
    });

    const nodes = filteredNodes.map((node) => {
      const domainId = node.type === 'Domain' ? node.id : belongsTo.get(node.id);
      const domainColor = domainId ? domainColorMap.get(domainId) : undefined;
      return {
        ...node,
        domainId,
        domainColor,
        confidence: node.confidence ?? 0,
      };
    });

    return { nodes, links };
  }, [graph, filteredNodes]);

  useEffect(() => {
    initializedRef.current = false;
  }, [graphData]);

  useEffect(() => {
    if (!fgRef.current) return;
    const controls = fgRef.current.controls();
    if (!controls) return;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.5;
    controls.zoomSpeed = 0.6;
    controls.panSpeed = 0.5;
    controls.screenSpacePanning = true;
    controls.minDistance = 18;
    controls.maxDistance = 1000;
    controls.enablePan = true;
  }, [graphData]);

  const focusCameraOnNode = useCallback((node: any, distance: number, duration = 1200) => {
    if (!fgRef.current || !node) return;
    const camera = fgRef.current.camera();
    const target = new THREE.Vector3(node.x || 0, node.y || 0, node.z || 0);
    const current = camera
      ? new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z)
      : new THREE.Vector3(0, 0, distance);
    const direction = current.sub(target).normalize();
    if (Number.isNaN(direction.x)) {
      direction.set(1, 0.6, 0.8).normalize();
    }
    const newPos = target.clone().add(direction.multiplyScalar(distance));
    fgRef.current.cameraPosition(newPos, target, duration);
  }, []);

  const resetCamera = useCallback(() => {
    if (!fgRef.current || !graphData.nodes.length) return;
    const nodes = graphData.nodes;
    const center = nodes.reduce((acc, node: any) => {
      acc.x += node.x || 0;
      acc.y += node.y || 0;
      acc.z += node.z || 0;
      return acc;
    }, new THREE.Vector3(0, 0, 0));
    center.divideScalar(nodes.length || 1);
    const maxDistance = nodes.reduce((max: number, node: any) => {
      const dx = (node.x || 0) - center.x;
      const dy = (node.y || 0) - center.y;
      const dz = (node.z || 0) - center.z;
      return Math.max(max, Math.sqrt(dx * dx + dy * dy + dz * dz));
    }, 1);
    const distance = Math.min(Math.max(maxDistance * 4, 220), 720);
    const startPos = new THREE.Vector3(center.x + distance, center.y + distance * 0.6, center.z + distance);
    fgRef.current.cameraPosition(startPos, center, 1400);
  }, [graphData.nodes]);

  useEffect(() => {
    if (!fgRef.current || graphData.nodes.length === 0) return;
    const camera = fgRef.current.camera();
    if (!camera) return;
    if (!initializedRef.current) {
      fgRef.current.cameraPosition(
        new THREE.Vector3(0, 220, 360),
        new THREE.Vector3(0, 0, 0),
        0
      );
    }
  }, [graphData.nodes.length]);

  useEffect(() => {
    if (!fgRef.current) return;
    const scene = fgRef.current.scene();
    if (!scene) return;

    if (!gridRef.current) {
      const grid = new THREE.GridHelper(800, 24, 0x1f2937, 0x0f172a);
      grid.position.y = -60;
      if (Array.isArray(grid.material)) {
        grid.material.forEach((material: any) => {
          material.transparent = true;
          material.opacity = 0.18;
        });
      } else {
        grid.material.transparent = true;
        grid.material.opacity = 0.18;
      }
      scene.add(grid);
      gridRef.current = grid;
    }

    if (!lightRef.current) {
      const ambient = new THREE.AmbientLight(0xffffff, 0.75);
      scene.add(ambient);
      lightRef.current = ambient;
    }

    // Setup CSS2D renderer for domain labels
    if (!css2dRendererRef.current && fgRef.current) {
      const renderer = fgRef.current.renderer();
      if (renderer && renderer.domElement && renderer.domElement.parentElement) {
        const css2dRenderer = new CSS2DRenderer();
        css2dRenderer.setSize(renderer.domElement.parentElement.clientWidth, renderer.domElement.parentElement.clientHeight);
        css2dRenderer.domElement.style.position = 'absolute';
        css2dRenderer.domElement.style.top = '0';
        css2dRenderer.domElement.style.pointerEvents = 'none';
        renderer.domElement.parentElement.appendChild(css2dRenderer.domElement);
        css2dRendererRef.current = css2dRenderer;
      }
    }

    // Update CSS2D labels on animation frame
    const updateLabels = () => {
      if (css2dRendererRef.current && fgRef.current) {
        const camera = fgRef.current.camera();
        if (camera) {
          css2dRendererRef.current.render(scene, camera);
        }
      }
      requestAnimationFrame(updateLabels);
    };
    const animationId = requestAnimationFrame(updateLabels);

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [graphData]);

  // Handle window resize for CSS2D renderer
  useEffect(() => {
    const handleResize = () => {
      if (css2dRendererRef.current && fgRef.current) {
        const renderer = fgRef.current.renderer();
        if (renderer && renderer.domElement && renderer.domElement.parentElement) {
          const width = renderer.domElement.parentElement.clientWidth;
          const height = renderer.domElement.parentElement.clientHeight;
          css2dRendererRef.current.setSize(width, height);
        }
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading 3D knowledge graph..." />
      </div>
    );
  }

  return (
    <div className="w-full h-full" style={{ minHeight: '500px' }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        backgroundColor="#0b0f1a"
        showNavInfo={true}
        linkColor={() => 'rgba(148, 163, 184, 0.7)'}
        linkWidth={1.2}
        nodeLabel={(node: any) => node.label || node.name}
        nodeRelSize={4}
        cooldownTime={1500}
        enableNodeDrag={false}
        onNodeClick={(node: any) => {
          setSelectedNode(node);
          if (onNodeSelect) {
            onNodeSelect(node.id);
          }

          if (node.type === 'Domain') {
            const now = Date.now();
            const lastClick = lastClickRef.current;
            const isDouble = lastClick && lastClick.id === node.id && now - lastClick.ts < 320;
            lastClickRef.current = { id: node.id, ts: now };
            const distance = isDouble ? 35 : 90;
            focusCameraOnNode(node, distance, isDouble ? 900 : 1400);
          }
        }}
        onBackgroundClick={() => setSelectedNode(null)}
        onEngineStop={() => {
          if (!initializedRef.current) {
            resetCamera();
            const controls = fgRef.current?.controls();
            if (controls) {
              controls.autoRotate = true;
              controls.autoRotateSpeed = 0.4;
              setTimeout(() => {
                if (controls) controls.autoRotate = false;
              }, 2800);
            }
            initializedRef.current = true;
          }
        }}
        nodeThreeObject={(node: any) => {
          if (node.type === 'Domain') {
            const group = new THREE.Group();
            const haloColor = node.domainColor || '#60a5fa';

            const halo = new THREE.Mesh(
              new THREE.SphereGeometry(28, 32, 32),
              new THREE.MeshBasicMaterial({
                color: haloColor,
                transparent: true,
                opacity: 0.18,
                depthWrite: false,
              })
            );
            group.add(halo);

            // Create CSS2D label for always-visible domain labels
            if (!labelObjectsRef.current.has(node.id)) {
              const labelDiv = document.createElement('div');
              labelDiv.className = 'domain-label';
              labelDiv.textContent = node.label || node.name || node.id;
              labelDiv.style.cssText = `
                color: ${haloColor};
                background: rgba(11, 15, 26, 0.85);
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                white-space: nowrap;
                pointer-events: none;
                border: 1px solid ${haloColor}40;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                backdrop-filter: blur(4px);
              `;
              const css2dLabel = new CSS2DObject(labelDiv);
              css2dLabel.position.set(0, 38, 0);
              labelObjectsRef.current.set(node.id, css2dLabel);
              group.add(css2dLabel);
            } else {
              const existingLabel = labelObjectsRef.current.get(node.id);
              if (existingLabel) {
                group.add(existingLabel);
              }
            }

            return group;
          }

          const color = node.domainColor || getConfidenceColor(node.confidence || 0);
          const size = 2 + (node.confidence || 0) * 4;
          const sphere = new THREE.Mesh(
            new THREE.SphereGeometry(size, 16, 16),
            new THREE.MeshStandardMaterial({ color })
          );

          const label = new SpriteText(node.label || node.name || node.id);
          label.color = '#e2e8f0';
          label.textHeight = 2.5;
          label.position.set(0, size + 3, 0);

          const group = new THREE.Group();
          group.add(sphere);
          group.add(label);

          return group;
        }}
        nodeThreeObjectExtend={false}
      />
      <div className="absolute bottom-4 right-4 pointer-events-auto">
        <button
          onClick={resetCamera}
          className="px-3 py-2 text-xs font-semibold uppercase tracking-wide bg-white/90 dark:bg-gray-900/80 text-gray-800 dark:text-gray-100 rounded-lg shadow-lg border border-white/40 hover:bg-white transition-colors"
        >
          Reset View
        </button>
      </div>
    </div>
  );
};
