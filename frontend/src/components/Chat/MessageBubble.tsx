import React from 'react';
import { User, Bot, ExternalLink, Tag } from 'lucide-react';
import { format } from 'date-fns';
import type { ChatMessage } from '../../types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-sm rounded-full">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isUser ? 'bg-blue-500' : 'bg-purple-500'}
      `}>
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-2xl ${isUser ? 'items-end' : ''}`}>
        <div className={`
          p-4 rounded-lg
          ${isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
          }
        `}>
          <p className="whitespace-pre-wrap">{message.content}</p>

          {/* Related Topics */}
          {message.relatedTopics && message.relatedTopics.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <Tag size={14} />
                <span className="text-sm font-semibold">Related Topics:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {message.relatedTopics.map((topic, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-full"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Resources */}
          {message.resources && message.resources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="text-sm font-semibold mb-2">Sources:</div>
              <ul className="space-y-1">
                {message.resources.map((resource, idx) => (
                  <li key={idx}>
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm flex items-center gap-2 hover:underline"
                    >
                      <ExternalLink size={12} />
                      <span>{resource.title}</span>
                      {resource.page && (
                        <span className="text-xs opacity-70">(p. {resource.page})</span>
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Quiz Result */}
          {message.quiz?.answered && (
            <div className={`
              mt-3 pt-3 border-t border-gray-200 dark:border-gray-700
              ${message.quiz.isCorrect ? 'text-green-600' : 'text-red-600'}
            `}>
              <div className="text-sm font-semibold">
                {message.quiz.isCorrect ? '✓ Correct!' : '✗ Incorrect'}
              </div>
              <p className="text-sm mt-1">{message.quiz.explanation}</p>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : ''}`}>
          {format(message.timestamp, 'HH:mm')}
        </div>
      </div>
    </div>
  );
};
