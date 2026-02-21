import React from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Filter, 
  Layout,
  Search,
  RefreshCw
} from 'lucide-react';
import { useGraph } from '../../hooks/useGraph';
import type { GraphLayout } from '../../types/curriculum';

export const GraphControls: React.FC = () => {
  const { 
    filter, 
    layout, 
    searchQuery,
    curriculumKey,
    availableCurricula,
    viewMode,
    setFilter, 
    setLayout, 
    setSearchQuery,
    setViewMode,
    setActiveCurriculum,
    fetchGraph,
    stats
  } = useGraph();

  const layouts: Array<{ name: GraphLayout['name']; label: string }> = [
    { name: 'cola', label: 'Force Directed' },
    { name: 'dagre', label: 'Hierarchical' },
    { name: 'circle', label: 'Circle' },
    { name: 'grid', label: 'Grid' },
  ];

  const handleLayoutChange = (layoutName: GraphLayout['name']) => {
    setLayout({
      name: layoutName,
      animate: true,
      fit: true,
    });
  };

  const curriculumOptions = availableCurricula.map((key) => {
    if (key === 'ukmla') {
      return { value: key, label: 'UKMLA' };
    }
    if (key === 'uk_legacy') {
      return { value: key, label: 'UK (Legacy)' };
    }
    if (key === 'uploaded') {
      return { value: key, label: 'Uploaded' };
    }
    return { value: key, label: key.toUpperCase() };
  });

  const activeCurriculumLabel = curriculumOptions.find(
    (option) => option.value === curriculumKey
  )?.label;

  return (
    <div className="absolute top-4 left-4 right-4 flex flex-col gap-3 pointer-events-none">
      {/* Search Bar */}
      <div className="flex gap-3">
        <div className="flex-1 pointer-events-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search topics..."
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          onClick={fetchGraph}
          className="pointer-events-auto px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Refresh graph"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Control Panel */}
      <div className="flex gap-3">
        {/* View Mode Toggle */}
        <div className="pointer-events-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-1 flex items-center gap-1">
          <button
            onClick={() => setViewMode('2d')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${viewMode === '2d' ? 'bg-blue-500 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
          >
            2D
          </button>
          <button
            onClick={() => setViewMode('3d')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${viewMode === '3d' ? 'bg-blue-500 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
          >
            3D
          </button>
        </div>

        {/* Curriculum Selector */}
        <div className="pointer-events-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-2">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Curriculum</span>
            <select
              value={curriculumKey || ''}
              onChange={(e) => setActiveCurriculum(e.target.value)}
              className="bg-transparent text-sm focus:outline-none cursor-pointer"
              disabled={curriculumOptions.length === 0}
            >
              {curriculumOptions.length === 0 ? (
                <option value="">Unavailable</option>
              ) : (
                curriculumOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {/* Active Curriculum Badge */}
        {activeCurriculumLabel && (
          <div className="pointer-events-auto flex items-center">
            <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200 border border-blue-200 dark:border-blue-800">
              {activeCurriculumLabel}
            </span>
          </div>
        )}

        {/* Layout Selector */}
        <div className="pointer-events-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-2">
          <div className="flex items-center gap-2">
            <Layout size={18} className="text-gray-600 dark:text-gray-400" />
            <select
              value={layout.name}
              onChange={(e) => handleLayoutChange(e.target.value as GraphLayout['name'])}
              className="bg-transparent text-sm focus:outline-none cursor-pointer"
            >
              {layouts.map(l => (
                <option key={l.name} value={l.name}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="pointer-events-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-2 flex items-center gap-3">
          <Filter size={18} className="text-gray-600 dark:text-gray-400" />
          
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={filter.showMastered ?? true}
              onChange={(e) => setFilter({ showMastered: e.target.checked })}
              className="rounded"
            />
            <span>Mastered</span>
          </label>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={filter.showUnreviewed ?? true}
              onChange={(e) => setFilter({ showUnreviewed: e.target.checked })}
              className="rounded"
            />
            <span>Unreviewed</span>
          </label>

          <div className="flex items-center gap-2">
            <span className="text-sm">Min Confidence:</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filter.minConfidence ?? 0}
              onChange={(e) => setFilter({ minConfidence: parseFloat(e.target.value) })}
              className="w-24"
            />
            <span className="text-sm font-medium">
              {((filter.minConfidence ?? 0) * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="pointer-events-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg px-4 py-2 flex items-center gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Topics: </span>
              <span className="font-semibold">{stats.totalNodes}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Avg: </span>
              <span className="font-semibold">{(stats.averageConfidence * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="font-semibold">{stats.masteredCount}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="font-semibold">{stats.lowConfidenceCount}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
