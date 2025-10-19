'use client';

import { useState, useEffect } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { SessionManager } from '@/lib/session';

interface TopicMastery {
  topic: string;
  mastery_score: number;
  quizzes_taken: number;
}

interface MasteryData {
  mastery: TopicMastery[];
  overall_skill_level: string;
  knowledge_gaps?: string[];
  strengths?: string[];
}

export default function MasteryRadar() {
  const [masteryData, setMasteryData] = useState<MasteryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMasteryData();
  }, []);

  const loadMasteryData = async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch('http://localhost:8007/adaptive/mastery', {
        headers: {
          'x-user-key': userId,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load mastery data');
      }

      const data = await response.json();
      setMasteryData(data);
    } catch (err) {
      setError('Failed to load mastery data');
      console.error('Mastery load error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !masteryData || !masteryData.mastery || masteryData.mastery.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Mastery Overview
        </h2>
        <div className="text-center py-12">
          <div className="text-5xl mb-3">📊</div>
          <p className="text-gray-600 dark:text-gray-400">
            {error || 'Take quizzes to see your mastery radar chart'}
          </p>
        </div>
      </div>
    );
  }

  // Transform data for radar chart
  const chartData = masteryData.mastery.map(topic => ({
    topic: topic.topic.length > 20 ? topic.topic.substring(0, 20) + '...' : topic.topic,
    fullTopic: topic.topic,
    mastery: Math.round(topic.mastery_score),
    quizzes: topic.quizzes_taken,
  }));

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Mastery Overview
      </h2>

      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={chartData}>
            <PolarGrid stroke="#60a5fa" strokeOpacity={0.5} />
            <PolarAngleAxis
              dataKey="topic"
              tick={{ fill: '#e5e7eb', fontSize: 12, fontWeight: 500 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#d1d5db', fontSize: 11 }}
            />
            <Radar
              name="Mastery %"
              dataKey="mastery"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.7}
              strokeWidth={2}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-gray-900 dark:bg-gray-800 p-3 rounded-lg shadow-xl border-2 border-blue-500">
                      <p className="font-semibold text-white mb-1">
                        {data.fullTopic}
                      </p>
                      <p className="text-blue-400 font-medium">
                        Mastery: {data.mastery}%
                      </p>
                      <p className="text-sm text-gray-300">
                        {data.quizzes} quiz{data.quizzes !== 1 ? 'zes' : ''} taken
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">
            No mastery data available
          </p>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-2 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span className="text-gray-700 dark:text-gray-200 font-medium">Mastery Score</span>
        </div>
      </div>
    </div>
  );
}
