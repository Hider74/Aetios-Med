import React, { useState } from 'react';
import { Folder, Plus, Trash2, CheckCircle } from 'lucide-react';
import { ipc } from '../../services/ipc';
import { useSettingsStore } from '../../stores/settingsStore';

export const FolderConfig: React.FC = () => {
  const { resourceFolders, addResourceFolder, removeResourceFolder } = useSettingsStore();
  const [isAdding, setIsAdding] = useState(false);

  const handleAddFolder = async () => {
    setIsAdding(true);
    try {
      const folderPath = await ipc.selectFolder();
      if (folderPath) {
        addResourceFolder(folderPath);
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Resource Folders
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Add folders containing your study materials (PDFs, videos, notes). 
          Aetios-Med will index and search through them.
        </p>
      </div>

      {/* Folder List */}
      <div className="space-y-3">
        {resourceFolders.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
            <Folder size={48} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No resource folders added yet
            </p>
            <button
              onClick={handleAddFolder}
              disabled={isAdding}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors inline-flex items-center gap-2"
            >
              <Plus size={18} />
              Add First Folder
            </button>
          </div>
        ) : (
          <>
            {resourceFolders.map((folder, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                  <Folder size={20} className="text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {folder}
                  </p>
                </div>
                <button
                  onClick={() => removeResourceFolder(folder)}
                  className="p-2 hover:bg-red-100 dark:hover:bg-red-900/20 rounded-lg text-red-600 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}

            {/* Add More Button */}
            <button
              onClick={handleAddFolder}
              disabled={isAdding}
              className="w-full py-3 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400"
            >
              <Plus size={18} />
              Add Another Folder
            </button>
          </>
        )}
      </div>

      {/* Info Box */}
      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
        <div className="flex gap-3">
          <CheckCircle className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
          <div className="text-sm text-green-800 dark:text-green-400">
            <p className="font-semibold mb-1">Supported Formats:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>PDF documents (.pdf)</li>
              <li>Text files (.txt, .md)</li>
              <li>Microsoft Word (.docx)</li>
              <li>PowerPoint presentations (.pptx)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Privacy Note */}
      <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-600 dark:text-gray-400">
          🔒 <strong>Privacy:</strong> All your files are processed locally on your device. 
          Nothing is uploaded to the cloud.
        </p>
      </div>
    </div>
  );
};
