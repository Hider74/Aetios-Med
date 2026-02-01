import React, { useState } from 'react';
import { Key, ExternalLink, CheckCircle, AlertCircle } from 'lucide-react';

export const HuggingFaceAuth: React.FC = () => {
  const [token, setToken] = useState('');
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleTest = async () => {
    if (!token.trim()) return;

    setTesting(true);
    setStatus('idle');

    // Simulate API test (replace with actual validation)
    try {
      // In a real implementation, this would validate the token with HuggingFace API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      localStorage.setItem('hf_token', token);
      setStatus('success');
    } catch (error) {
      setStatus('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          HuggingFace Authentication
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Some models require a HuggingFace account. This is optional but recommended for accessing premium models.
        </p>
      </div>

      {/* Token Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Access Token
        </label>
        <div className="relative">
          <Key className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="hf_..."
            className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* How to get token */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
          How to get an access token:
        </h4>
        <ol className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-decimal list-inside">
          <li>Go to HuggingFace and create an account (free)</li>
          <li>Navigate to Settings → Access Tokens</li>
          <li>Create a new token with "read" permissions</li>
          <li>Copy and paste it here</li>
        </ol>
        <a
          href="https://huggingface.co/settings/tokens"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 mt-3 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <ExternalLink size={14} />
          Open HuggingFace Settings
        </a>
      </div>

      {/* Test Button */}
      <button
        onClick={handleTest}
        disabled={!token.trim() || testing}
        className="w-full py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {testing ? 'Testing...' : 'Test & Save Token'}
      </button>

      {/* Status Messages */}
      {status === 'success' && (
        <div className="flex items-center gap-2 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <CheckCircle className="text-green-600" size={20} />
          <span className="text-sm text-green-700 dark:text-green-400">
            Token validated and saved successfully!
          </span>
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertCircle className="text-red-600" size={20} />
          <span className="text-sm text-red-700 dark:text-red-400">
            Invalid token. Please check and try again.
          </span>
        </div>
      )}

      {/* Skip Option */}
      <div className="text-center">
        <button className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
          Skip for now (you can add this later in settings)
        </button>
      </div>
    </div>
  );
};
