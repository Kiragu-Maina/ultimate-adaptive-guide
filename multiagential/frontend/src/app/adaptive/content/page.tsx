'use client';

import { useState, useEffect, Suspense, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { SessionManager } from '@/lib/session';
import mermaid from 'mermaid';
import { notifyContentReady } from '@/lib/notifications';
import MarkdownRenderer from '@/components/MarkdownRenderer';

interface Content {
  content: string;
  exercises: { description: string; type: string }[];
  resources: { title: string; url: string; type: string }[];
  diagram: string;
  difficulty: string;
  mastery?: {
    topic: string;
    skill_level: string;
    mastery_score: number;
    attempts: number;
    last_attempted: string | null;
  };
  agent_activity: { agent: string; action: string }[];
  description?: string;
}

function AdaptiveContentInner() {
  const searchParams = useSearchParams();
  const topic = searchParams.get('topic') || '';
  const [userId, setUserId] = useState<string>('');
  const [content, setContent] = useState<Content | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const mermaidRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Initialize Mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, sans-serif',
    });
  }, []);

  useEffect(() => {
    const sessionUserId = SessionManager.getUserId();
    setUserId(sessionUserId);

    if (topic && sessionUserId) {
      fetchContent(sessionUserId, topic);
    }
  }, [topic]);

  // Render Mermaid diagram when content changes
  useEffect(() => {
    if (content?.diagram && mermaidRef.current) {
      const renderMermaid = async () => {
        try {
          mermaidRef.current!.innerHTML = content.diagram;
          await mermaid.run({
            nodes: [mermaidRef.current!],
          });
        } catch (error) {
          console.error('Error rendering Mermaid diagram:', error);
          mermaidRef.current!.innerHTML = `
            <div class="text-red-600 text-sm p-4 bg-red-50 rounded border border-red-200">
              <p class="font-medium">Failed to render diagram</p>
              <p class="text-xs mt-1">The diagram code may have syntax errors.</p>
            </div>
          `;
        }
      };
      renderMermaid();
    }
  }, [content?.diagram]);

  const fetchContent = async (sessionUserId: string, topicName: string) => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(
        `http://localhost:8007/adaptive/content?topic=${encodeURIComponent(topicName)}&user_id=${sessionUserId}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch content');
      }

      const data = await response.json();
      console.log('Received data:', data);
      console.log('Content field:', data.content);
      console.log('Content type:', typeof data.content);
      setContent(data);

      // Show notification that content is ready
      if (data && topicName) {
        notifyContentReady(topicName);
      }
    } catch (err) {
      console.error('Error fetching content:', err);
      setError('Failed to load content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToJourney = () => {
    window.location.href = '/adaptive';
  };

  const handleMarkComplete = async () => {
    if (!userId || !topic) return;

    try {
      const response = await fetch('http://localhost:8007/adaptive/content/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Key': userId,
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error('Failed to mark topic as complete');
      }

      // On success, go back to the journey page
      handleBackToJourney();
    } catch (error) {
      console.error('Error marking topic as complete:', error);
      alert('There was an error marking this topic as complete. Please try again.');
    }
  };

  

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-6xl mb-4">🤖</div>
          <p className="text-gray-700 text-lg font-medium">Loading adaptive content...</p>
          <p className="text-gray-600 text-sm mt-2">AI agents are personalizing this for you</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Not Available</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleBackToJourney}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            ← Back to Learning Journey
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBackToJourney}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Journey
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-xl font-bold text-gray-900">{topic}</h1>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full font-medium">
              🤖 Adaptive Content
            </span>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto py-8 px-6">
        {content ? (
          <div className="space-y-8">
            {/* Content Header */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">{topic}</h2>

              {content.difficulty && (
                <div className="flex items-center space-x-2 mb-4">
                  <span className="text-sm text-gray-600">Difficulty:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    content.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                    content.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {content.difficulty.charAt(0).toUpperCase() + content.difficulty.slice(1)}
                  </span>
                </div>
              )}

              {content.description && (
                <p className="text-gray-700 text-lg leading-relaxed">{content.description}</p>
              )}
            </div>

            {/* Main Content */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
              <div className="max-w-none">
                {content.content ? (
                  <div ref={contentRef} className="max-w-none">
                    <MarkdownRenderer>{content.content}</MarkdownRenderer>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-600 dark:text-gray-400">
                      Content for this topic is being generated by our AI agents.
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Please check back later or contact support if this persists.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Diagram Section */}
            {content.diagram && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">📊 Visual Diagram</h3>
                <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 flex justify-center">
                  <div
                    ref={mermaidRef}
                    className="mermaid"
                    style={{ minHeight: '200px' }}
                  >
                    {/* Mermaid will render here */}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-3 text-center">
                  Created by 🤖 Diagram Generator Agent
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between items-center pt-6 border-t">
              <button
                onClick={handleBackToJourney}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                ← Back to Journey
              </button>

              <div className="flex space-x-4">
                <button
                  onClick={() => {
                    window.location.href = `/practice/quiz?topic=${encodeURIComponent(topic)}`;
                  }}
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
                >
                  Take Quiz 📝
                </button>
                <button
                  onClick={handleMarkComplete}
                  className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
                >
                  Mark Complete ✓
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Content Available</h2>
            <p className="text-gray-600 mb-6">
              We couldn&apos;t load the content for this topic.
            </p>
            <button
              onClick={handleBackToJourney}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              ← Back to Learning Journey
            </button>
          </div>
        )}
      </main>

      {/* Agent Attribution Footer */}
      <footer className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-6 mt-12">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-sm">
            This content was personalized for you by:
          </p>
          <div className="flex justify-center space-x-8 mt-3">
            <div className="text-xs">
              <div className="text-lg mb-1">🤖</div>
              <div>Content Personalizer</div>
            </div>
            <div className="text-xs">
              <div className="text-lg mb-1">📊</div>
              <div>Performance Analyzer</div>
            </div>
            <div className="text-xs">
              <div className="text-lg mb-1">📐</div>
              <div>Diagram Generator</div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function AdaptiveContentPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-6xl mb-4">🤖</div>
          <p className="text-gray-700 text-lg font-medium">Loading...</p>
        </div>
      </div>
    }>
      <AdaptiveContentInner />
    </Suspense>
  );
}
