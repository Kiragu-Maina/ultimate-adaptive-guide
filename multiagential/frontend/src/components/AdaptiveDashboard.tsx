'use client';

import { useState, useEffect } from 'react';
import { SessionManager } from '@/lib/session';

interface LearnerProfile {
  overall_skill_level: string;
  priority_topics: string[];
  learning_pace: string;
  confidence: number;
  profile_summary: string;
}

interface JourneyTopic {
  topic: string;
  position: number;
  status: string;
  estimated_hours: number;
  reasoning: string;
  is_milestone?: boolean;
  milestone_name?: string;
}

interface Recommendation {
  topic: string;
  reasoning: string;
  source: string;
  composite_score: number;
}

interface RecommendationsData {
  recommendations: Recommendation[];
  reasoning: string;
  confidence: number;
}

interface AdaptiveDashboardProps {
  profile: LearnerProfile | null;
  journey: JourneyTopic[];
  onStartTopic?: (topic: string) => void;
}

export default function AdaptiveDashboard({ profile, journey, onStartTopic }: AdaptiveDashboardProps) {
  const [recommendations, setRecommendations] = useState<RecommendationsData | null>(null);

  useEffect(() => {
    // Get user session
    const sessionUserId = SessionManager.getUserId();

    if (profile) {
      fetchRecommendations(sessionUserId);
    }
  }, [profile]);

  const fetchRecommendations = async (sessionUserId: string) => {
    try {
      const response = await fetch(`http://localhost:8007/adaptive/recommendations?user_id=${sessionUserId}`);
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'in_progress': return 'bg-blue-500';
      case 'available': return 'bg-yellow-500';
      default: return 'bg-gray-300';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'in_progress': return '▶';
      case 'available': return '○';
      default: return '●';
    }
  };

  const completedCount = journey.filter(t => t.status === 'completed').length;
  const progressPercentage = (completedCount / journey.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            🎓 Your Adaptive Learning Dashboard
          </h1>
          <p className="text-gray-600">
            Powered by AI agents that personalize your learning experience
          </p>
        </div>

        {/* Profile Summary */}
        {profile && (
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-md p-6 text-white">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-bold mb-2">Your Learning Profile</h2>
                <p className="text-blue-100 mb-4">{profile.profile_summary}</p>

                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-blue-100">Skill Level</div>
                    <div className="text-lg font-bold capitalize">{profile.overall_skill_level}</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-blue-100">Learning Pace</div>
                    <div className="text-lg font-bold capitalize">{profile.learning_pace}</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-blue-100">AI Confidence</div>
                    <div className="text-lg font-bold">{profile.confidence}%</div>
                  </div>
                </div>
              </div>

              <div className="ml-4 bg-white/20 rounded-lg p-4">
                <div className="text-sm text-blue-100 mb-1">Created by</div>
                <div className="text-lg font-bold">🤖 Learner</div>
                <div className="text-lg font-bold">Profiler Agent</div>
              </div>
            </div>

            {profile.priority_topics && profile.priority_topics.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/30">
                <div className="text-sm text-blue-100 mb-2">Priority Topics:</div>
                <div className="flex flex-wrap gap-2">
                  {profile.priority_topics.map((topic, idx) => (
                    <span key={idx} className="px-3 py-1 bg-white/30 rounded-full text-sm">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Progress Overview */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Learning Progress</h2>

          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{completedCount} of {journey.length} topics completed</span>
              <span>{Math.round(progressPercentage)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 mt-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{completedCount}</div>
              <div className="text-sm text-gray-600 mt-1">Completed</div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">
                {journey.filter(t => t.status === 'in_progress').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">In Progress</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {journey.filter(t => t.status === 'available').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Available</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-gray-600">
                {journey.reduce((sum, t) => sum + (t.estimated_hours || 0), 0)}h
              </div>
              <div className="text-sm text-gray-600 mt-1">Total Hours</div>
            </div>
          </div>
        </div>

        {/* Learning Journey */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-800">Your Learning Journey</h2>
              <p className="text-sm text-gray-600 mt-1">
                Designed by <span className="font-semibold text-purple-600">🤖 Journey Architect Agent</span>
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {journey.map((topic, idx) => (
              <div key={idx} className="relative">
                {/* Milestone marker */}
                {topic.is_milestone && (
                  <div className="absolute -left-2 top-1/2 transform -translate-y-1/2 z-10">
                    <div className="bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold flex items-center">
                      ⭐ {topic.milestone_name}
                    </div>
                  </div>
                )}

                <div
                  className={`flex items-center p-4 rounded-lg border-2 transition-all ${
                    topic.status === 'available'
                      ? 'border-blue-300 bg-blue-50 hover:bg-blue-100 cursor-pointer'
                      : topic.status === 'completed'
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300 bg-gray-50'
                  }`}
                  onClick={() => {
                    if (topic.status === 'available' && onStartTopic) {
                      onStartTopic(topic.topic);
                    }
                  }}
                >
                  {/* Position & Status */}
                  <div className={`w-10 h-10 rounded-full ${getStatusColor(topic.status)} text-white flex items-center justify-center font-bold mr-4 flex-shrink-0`}>
                    {getStatusIcon(topic.status)}
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-gray-800">{topic.topic}</h3>
                      <span className="text-sm text-gray-500">{topic.estimated_hours}h</span>
                    </div>
                    <p className="text-sm text-gray-600">{topic.reasoning}</p>
                  </div>

                  {/* Action button */}
                  {topic.status === 'available' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onStartTopic) {
                          onStartTopic(topic.topic);
                        }
                      }}
                      className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Start →
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Recommendations */}
        {recommendations && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-800">Smart Recommendations</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Powered by <span className="font-semibold text-indigo-600">🤖 Recommendation Agent</span>
                </p>
              </div>
              <div className="text-sm text-gray-500">
                {recommendations.confidence && `${Math.round(recommendations.confidence * 100)}% confident`}
              </div>
            </div>

            {recommendations.reasoning && (
              <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-line">{recommendations.reasoning}</p>
              </div>
            )}

            {recommendations.recommendations && recommendations.recommendations.length > 0 && (
              <div className="space-y-2">
                {recommendations.recommendations.map((rec: Recommendation, idx: number) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800">{rec.topic}</h3>
                        <p className="text-sm text-gray-600 mt-1">{rec.reasoning}</p>
                        {rec.source && (
                          <span className="inline-block mt-2 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                            {rec.source.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      {rec.composite_score && (
                        <div className="ml-4 text-center">
                          <div className="text-2xl font-bold text-indigo-600">
                            {Math.round(rec.composite_score)}
                          </div>
                          <div className="text-xs text-gray-500">score</div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Agent Activity Info */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg shadow-md p-6 text-white">
          <h2 className="text-xl font-bold mb-3">🤖 Multi-Agent System Active</h2>
          <p className="text-purple-100 mb-4">
            Your learning experience is powered by 8 specialized AI agents working together:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              'Learner Profiler',
              'Journey Architect',
              'Performance Analyzer',
              'Recommendation',
              'Quiz Generator',
              'Content Personalizer',
              'Motivation',
              'Diagram Generator'
            ].map((agent) => (
              <div key={agent} className="bg-white/20 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">🤖</div>
                <div className="text-xs font-medium">{agent}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
