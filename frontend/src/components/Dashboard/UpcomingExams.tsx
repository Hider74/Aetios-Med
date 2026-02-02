import React, { useState, useEffect } from 'react';
import { Calendar, Plus, Edit, Trash2, X } from 'lucide-react';
import { format, differenceInDays } from 'date-fns';
import { api } from '../../services/api';
import { useGraph } from '../../hooks/useGraph';
import type { Exam } from '../../types/study';

export const UpcomingExams: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    date: '',
    topics: [] as string[],
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
  });
  const { graph } = useGraph();

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const data = await api.getExams();
      // Sort by date, soonest first
      const sorted = data.sort((a, b) => a.date.getTime() - b.date.getTime());
      setExams(sorted.slice(0, 5)); // Show only next 5
    } catch (error) {
      console.error('Failed to load exams:', error);
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditingExam(null);
    setFormData({
      name: '',
      date: '',
      topics: [],
      priority: 'medium',
    });
    setShowModal(true);
  };

  const openEditModal = (exam: Exam) => {
    setEditingExam(exam);
    setFormData({
      name: exam.name,
      date: format(exam.date, 'yyyy-MM-dd'),
      topics: exam.topics,
      priority: exam.priority,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingExam(null);
    setFormData({
      name: '',
      date: '',
      topics: [],
      priority: 'medium',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingExam) {
        // Update existing exam
        await api.updateExam(editingExam.id, {
          ...formData,
          date: new Date(formData.date),
        });
      } else {
        // Create new exam
        await api.createExam({
          ...formData,
          date: new Date(formData.date),
          completed: false,
        });
      }
      
      await loadExams();
      closeModal();
    } catch (error) {
      console.error('Failed to save exam:', error);
      alert('Failed to save exam. Please try again.');
    }
  };

  const handleDelete = async (examId: string) => {
    if (!confirm('Are you sure you want to delete this exam?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8741/api/study/exam/${examId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete exam');
      }
      
      await loadExams();
    } catch (error) {
      console.error('Failed to delete exam:', error);
      alert('Failed to delete exam. Please try again.');
    }
  };

  const toggleTopic = (topicId: string) => {
    setFormData(prev => ({
      ...prev,
      topics: prev.topics.includes(topicId)
        ? prev.topics.filter(t => t !== topicId)
        : [...prev.topics, topicId],
    }));
  };

  const availableTopics = graph?.nodes || [];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
      case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low': return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getDaysUntil = (date: Date) => {
    const days = differenceInDays(date, new Date());
    if (days < 0) return 'Past due';
    if (days === 0) return 'Today!';
    if (days === 1) return 'Tomorrow';
    return `${days} days`;
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calendar size={20} className="text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Upcoming Exams
            </h3>
          </div>
          <button 
            onClick={openAddModal}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Plus size={18} />
          </button>
        </div>

      {/* Exams List */}
      {exams.length === 0 ? (
        <div className="text-center py-8">
          <Calendar size={48} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">No upcoming exams</p>
          <button 
            onClick={openAddModal}
            className="mt-3 text-sm text-blue-500 hover:text-blue-600"
          >
            Add your first exam
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {exams.map((exam) => {
            const daysUntil = getDaysUntil(exam.date);
            const isUrgent = differenceInDays(exam.date, new Date()) <= 7;

            return (
              <div
                key={exam.id}
                className={`
                  p-4 rounded-lg border-2 transition-all hover:shadow-md
                  ${isUrgent 
                    ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10' 
                    : 'border-gray-200 dark:border-gray-700'
                  }
                `}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {exam.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {format(exam.date, 'MMMM dd, yyyy')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(exam.priority)}`}>
                      {exam.priority}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className={`text-sm font-medium ${isUrgent ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400'}`}>
                      {daysUntil}
                    </span>
                    <span className="text-xs text-gray-500">
                      {exam.topics.length} topics
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <button 
                      onClick={() => openEditModal(exam)}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                    >
                      <Edit size={14} />
                    </button>
                    <button 
                      onClick={() => handleDelete(exam.id)}
                      className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded text-red-600"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>

    {/* Modal */}
    {showModal && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Modal Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              {editingExam ? 'Edit Exam' : 'Add New Exam'}
            </h2>
            <button 
              onClick={closeModal}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Modal Body */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Exam Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="e.g., Anatomy Midterm"
              />
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Exam Date *
              </label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as any }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            {/* Topics */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Topics
              </label>
              <div className="border border-gray-300 dark:border-gray-600 rounded-lg p-3 max-h-64 overflow-y-auto bg-white dark:bg-gray-700">
                {availableTopics.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">No topics available</p>
                ) : (
                  <div className="space-y-2">
                    {availableTopics.map((topic) => (
                      <label 
                        key={topic.id}
                        className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600 p-2 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={formData.topics.includes(topic.id)}
                          onChange={() => toggleTopic(topic.id)}
                          className="w-4 h-4 text-blue-500 rounded"
                        />
                        <span className="text-sm text-gray-900 dark:text-white">{topic.label}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {formData.topics.length} topic(s) selected
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={closeModal}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
              >
                {editingExam ? 'Update Exam' : 'Add Exam'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )}
  </>
  );
};
