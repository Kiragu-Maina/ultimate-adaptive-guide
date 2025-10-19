'use client';

import Link from 'next/link';

interface Milestone {
  title: string;
  topics: string[];
  status: 'completed' | 'current' | 'locked';
  order: number;
}

interface MilestoneCardProps {
  milestone: Milestone;
  progress?: number;
}

export default function MilestoneCard({ milestone, progress = 0 }: MilestoneCardProps) {
  const statusConfig = {
    completed: {
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-500',
      iconBg: 'bg-green-500',
      icon: '✓',
      textColor: 'text-green-700 dark:text-green-300',
      badgeColor: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    },
    current: {
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      borderColor: 'border-blue-500',
      iconBg: 'bg-blue-500',
      icon: '▶',
      textColor: 'text-blue-700 dark:text-blue-300',
      badgeColor: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    },
    locked: {
      bgColor: 'bg-gray-50 dark:bg-gray-800/50',
      borderColor: 'border-gray-300 dark:border-gray-700',
      iconBg: 'bg-gray-400 dark:bg-gray-600',
      icon: '🔒',
      textColor: 'text-gray-500 dark:text-gray-400',
      badgeColor: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
    },
  };

  const config = statusConfig[milestone.status];

  return (
    <div className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-lg p-6 hover:shadow-lg transition-all`}>
      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className={`flex-shrink-0 w-12 h-12 ${config.iconBg} rounded-full flex items-center justify-center text-white text-xl font-bold shadow-md`}>
          {config.icon}
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                {milestone.title}
              </h3>
              <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${config.badgeColor}`}>
                {milestone.status === 'completed'
                  ? 'Completed'
                  : milestone.status === 'current'
                  ? 'In Progress'
                  : 'Locked'}
              </span>
            </div>
          </div>

          {/* Topics */}
          <div className="mb-4">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Topics ({milestone.topics.length}):
            </p>
            <div className="flex flex-wrap gap-2">
              {milestone.topics.map((topic, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full text-sm text-gray-700 dark:text-gray-300"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>

          {/* Progress Bar (for current milestone) */}
          {milestone.status === 'current' && progress > 0 && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Progress
                </span>
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {milestone.status !== 'locked' && milestone.topics.length > 0 && (
            <div className="flex gap-2">
              <Link
                href={`/adaptive/content?topic=${encodeURIComponent(milestone.topics[0])}`}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                  milestone.status === 'completed'
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {milestone.status === 'completed' ? 'Review' : 'Start Learning'}
              </Link>

              {milestone.status === 'current' && (
                <Link
                  href="/practice"
                  className="px-4 py-2 bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg font-semibold hover:bg-blue-50 dark:hover:bg-gray-600 transition-colors"
                >
                  Practice
                </Link>
              )}
            </div>
          )}

          {milestone.status === 'locked' && (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              Complete previous milestones to unlock
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
