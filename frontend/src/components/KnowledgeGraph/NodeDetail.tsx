import React, { useState } from 'react';
import { 
  X, 
  BookOpen, 
  Calendar, 
  TrendingUp, 
  Edit, 
  Trash2,
  ExternalLink,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useGraph } from '../../hooks/useGraph';
import { formatDistanceToNow } from 'date-fns';
import type { TopicNode } from '../../types/curriculum';

interface NodeDetailProps {
  onClose: () => void;
  onStartStudy?: (topicId: string) => void;
}

export const NodeDetail: React.FC<NodeDetailProps> = ({ onClose, onStartStudy }) => {
  const { selectedNode, updateNodeConfidence, deleteNode, getRelatedNodes } = useGraph();
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfidence, setEditedConfidence] = useState(selectedNode?.confidence || 0);

  if (!selectedNode) return null;

  const relatedNodes = getRelatedNodes(selectedNode.id);

  const handleSaveConfidence = async () => {
    await updateNodeConfidence(selectedNode.id, editedConfidence);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (confirm(`Delete topic "${selectedNode.label}"?`)) {
      await deleteNode(selectedNode.id);
      onClose();
    }
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence <= 0.3) return { label: 'Low', color: 'text-red-500' };
    if (confidence <= 0.6) return { label: 'Medium', color: 'text-yellow-500' };
    return { label: 'High', color: 'text-green-500' };
  };

  const confidenceInfo = getConfidenceLabel(selectedNode.confidence);

  return (
    <div className="absolute top-0 right-0 w-96 h-full bg-white dark:bg-gray-800 shadow-2xl border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-start justify-between z-10">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            {selectedNode.label}
          </h3>
          {selectedNode.mastered && (
            <div className="flex items-center gap-1 mt-1 text-sm text-green-600">
              <CheckCircle size={16} />
              <span>Mastered</span>
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Confidence */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <TrendingUp size={16} />
              Confidence Level
            </h4>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="text-sm text-blue-500 hover:text-blue-600"
            >
              {isEditing ? 'Cancel' : 'Edit'}
            </button>
          </div>
          
          {isEditing ? (
            <div className="space-y-3">
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={editedConfidence}
                onChange={(e) => setEditedConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">{(editedConfidence * 100).toFixed(0)}%</span>
                <button
                  onClick={handleSaveConfidence}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Save
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-baseline gap-2">
                <span className={`text-3xl font-bold ${confidenceInfo.color}`}>
                  {(selectedNode.confidence * 100).toFixed(0)}%
                </span>
                <span className="text-sm text-gray-500">{confidenceInfo.label}</span>
              </div>
              <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                  style={{ width: `${selectedNode.confidence * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Review Info */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2 mb-2">
            <Calendar size={16} />
            Review Status
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Times Reviewed:</span>
              <span className="font-semibold">{selectedNode.timesReviewed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Last Reviewed:</span>
              <span className="font-semibold">
                {selectedNode.lastReviewed 
                  ? formatDistanceToNow(selectedNode.lastReviewed, { addSuffix: true })
                  : 'Never'
                }
              </span>
            </div>
          </div>
        </div>

        {/* Notes */}
        {selectedNode.notes && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2 mb-2">
              <Edit size={16} />
              Notes
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
              {selectedNode.notes}
            </p>
          </div>
        )}

        {/* Resources */}
        {selectedNode.resources.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2 mb-2">
              <BookOpen size={16} />
              Resources
            </h4>
            <ul className="space-y-2">
              {selectedNode.resources.map((resource, idx) => (
                <li key={idx}>
                  <a
                    href={resource}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-500 hover:text-blue-600 flex items-center gap-2"
                  >
                    <ExternalLink size={14} />
                    {resource}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Related Topics */}
        {relatedNodes.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Related Topics ({relatedNodes.length})
            </h4>
            <div className="space-y-2">
              {relatedNodes.map(node => (
                <div
                  key={node.id}
                  className="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-between"
                >
                  <span className="text-sm">{node.label}</span>
                  <span className="text-xs font-semibold">
                    {(node.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          {onStartStudy && (
            <button
              onClick={() => onStartStudy(selectedNode.id)}
              className="w-full px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
            >
              Start Study Session
            </button>
          )}
          
          <button
            onClick={handleDelete}
            className="w-full px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
          >
            <Trash2 size={16} />
            Delete Topic
          </button>
        </div>
      </div>
    </div>
  );
};
