import React, { useState, useRef } from 'react';
import { ArrowLeft, ArrowRight, RefreshCw, ExternalLink, Home, X } from 'lucide-react';

interface WebViewPanelProps {
  url?: string;
  onClose?: () => void;
}

export const WebViewPanel: React.FC<WebViewPanelProps> = ({ url: initialUrl, onClose }) => {
  const [url, setUrl] = useState(initialUrl || 'https://www.ncbi.nlm.nih.gov/pubmed/');
  const [inputUrl, setInputUrl] = useState(url);
  const [loading, setLoading] = useState(false);
  const [canGoBack] = useState(false);
  const [canGoForward] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handleNavigate = () => {
    if (inputUrl.trim()) {
      let targetUrl = inputUrl.trim();
      if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
        targetUrl = 'https://' + targetUrl;
      }
      setUrl(targetUrl);
      setLoading(true);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNavigate();
    }
  };

  const handleRefresh = () => {
    if (iframeRef.current) {
      setLoading(true);
      iframeRef.current.src = iframeRef.current.src;
    }
  };

  const handleOpenExternal = () => {
    window.open(url, '_blank');
  };

  const quickLinks = [
    { name: 'PubMed', url: 'https://www.ncbi.nlm.nih.gov/pubmed/' },
    { name: 'Wikipedia Medical', url: 'https://en.wikipedia.org/wiki/Portal:Medicine' },
    { name: 'MedlinePlus', url: 'https://medlineplus.gov/' },
    { name: 'UpToDate', url: 'https://www.uptodate.com/' },
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Browser Controls */}
      <div className="flex items-center gap-2 p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        {/* Navigation Buttons */}
        <button
          onClick={() => window.history.back()}
          disabled={!canGoBack}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Back"
        >
          <ArrowLeft size={18} />
        </button>
        <button
          onClick={() => window.history.forward()}
          disabled={!canGoForward}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Forward"
        >
          <ArrowRight size={18} />
        </button>
        <button
          onClick={handleRefresh}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          title="Refresh"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
        <button
          onClick={() => setUrl('https://www.ncbi.nlm.nih.gov/pubmed/')}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          title="Home"
        >
          <Home size={18} />
        </button>

        {/* URL Bar */}
        <div className="flex-1 flex items-center gap-2">
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter URL..."
            className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button
            onClick={handleNavigate}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
          >
            Go
          </button>
        </div>

        {/* Actions */}
        <button
          onClick={handleOpenExternal}
          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          title="Open in external browser"
        >
          <ExternalLink size={18} />
        </button>
        
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
            title="Close"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Quick Links */}
      <div className="flex gap-2 p-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-x-auto">
        {quickLinks.map((link) => (
          <button
            key={link.name}
            onClick={() => {
              setUrl(link.url);
              setInputUrl(link.url);
            }}
            className="px-3 py-1 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors whitespace-nowrap"
          >
            {link.name}
          </button>
        ))}
      </div>

      {/* WebView */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-900 z-10">
            <div className="text-center">
              <RefreshCw className="animate-spin text-blue-500 mx-auto mb-2" size={32} />
              <p className="text-sm text-gray-600 dark:text-gray-400">Loading...</p>
            </div>
          </div>
        )}
        <iframe
          ref={iframeRef}
          src={url}
          className="w-full h-full border-0"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          onLoad={() => setLoading(false)}
          title="Resource Viewer"
        />
      </div>

      {/* Status Bar */}
      <div className="px-3 py-1 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-xs text-gray-600 dark:text-gray-400 flex items-center justify-between">
        <span className="truncate">{url}</span>
        <span>In-app Browser</span>
      </div>
    </div>
  );
};
