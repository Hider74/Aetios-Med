import React, { useState, useEffect } from 'react';
import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useModelStatus } from '../../hooks/useModelStatus';

const AVAILABLE_MODELS = [
  {
    name: 'BioMistral-7B',
    size: '4.1 GB',
    description: 'Recommended for medical studies. Best balance of performance and size.',
    recommended: true,
  },
  {
    name: 'Llama-2-7B-Medical',
    size: '3.8 GB',
    description: 'Alternative medical model with good performance.',
    recommended: false,
  },
  {
    name: 'Mistral-7B-Instruct',
    size: '4.1 GB',
    description: 'General purpose model with strong reasoning.',
    recommended: false,
  },
];

export const ModelDownload: React.FC = () => {
  const { status, downloadModel, checkStatus } = useModelStatus();
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0].name);

  useEffect(() => {
    checkStatus();
  }, []);

  const handleDownload = async () => {
    await downloadModel(selectedModel);
  };

  const getStatusIcon = () => {
    if (status.error) return <AlertCircle className="text-red-500" size={24} />;
    if (status.loaded) return <CheckCircle className="text-green-500" size={24} />;
    if (status.downloading) return <Loader2 className="text-blue-500 animate-spin" size={24} />;
    return <Download className="text-gray-400" size={24} />;
  };

  const getStatusText = () => {
    if (status.error) return `Error: ${status.error}`;
    if (status.loaded) return `Model loaded: ${status.model}`;
    if (status.downloading) return `Downloading... ${status.progress || 0}%`;
    return 'No model downloaded';
  };

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`
        p-4 rounded-lg border-2 flex items-center gap-4
        ${status.error ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' : ''}
        ${status.loaded ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' : ''}
        ${status.downloading ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800' : ''}
        ${!status.loaded && !status.downloading && !status.error ? 'bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-700' : ''}
      `}>
        {getStatusIcon()}
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white">{getStatusText()}</h4>
          {status.downloading && (
            <div className="mt-2">
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${status.progress || 0}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Model Selection */}
      {!status.loaded && !status.downloading && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Select AI Model
          </h3>
          <div className="space-y-3">
            {AVAILABLE_MODELS.map((model) => (
              <label
                key={model.name}
                className={`
                  block p-4 rounded-lg border-2 cursor-pointer transition-all
                  ${selectedModel === model.name
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="model"
                    value={model.name}
                    checked={selectedModel === model.name}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {model.name}
                      </h4>
                      {model.recommended && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400 text-xs rounded-full">
                          Recommended
                        </span>
                      )}
                      <span className="text-sm text-gray-500">({model.size})</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {model.description}
                    </p>
                  </div>
                </div>
              </label>
            ))}
          </div>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            disabled={status.downloading}
            className="w-full mt-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
          >
            <Download size={20} />
            Download {selectedModel}
          </button>

          {/* Info */}
          <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong>Note:</strong> Models are downloaded once and stored locally. 
              This may take several minutes depending on your internet connection. 
              Aetios-Med works completely offline after download.
            </p>
          </div>
        </div>
      )}

      {/* Success State */}
      {status.loaded && (
        <div className="text-center py-8">
          <CheckCircle size={64} className="text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Model Ready!
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {status.model} is loaded and ready to use.
          </p>
        </div>
      )}
    </div>
  );
};
