'use client';

import { useState, useEffect } from 'react';
import { SessionManager } from '@/lib/session';
import Link from 'next/link';

export default function Home() {
  const [hasAdaptiveProfile, setHasAdaptiveProfile] = useState(false);

  useEffect(() => {
    checkAdaptiveProfile();
  }, []);

  const checkAdaptiveProfile = () => {
    // Check if user has completed adaptive onboarding
    const userId = SessionManager.getUserId();
    const onboardingStatus = SessionManager.getOnboardingStatus();
    setHasAdaptiveProfile(onboardingStatus === userId);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white dark:bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                AlkenaCode School
              </h1>
              <span className="ml-3 px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 rounded-full">
                AI-Powered Learning
              </span>
              {hasAdaptiveProfile && (
                <span className="ml-2 px-3 py-1 text-sm bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded-full">
                  🤖 Adaptive Mode Active
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <Navigation hasProfile={hasAdaptiveProfile} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <DashboardView />
        </div>
      </main>

      {/* Chat Agent */}
      <ChatAgent />
    </div>
  );
}

function Navigation({ hasProfile }: { hasProfile: boolean }) {
  return (
    <nav className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          <Link
            href="/"
            className="py-4 px-1 border-b-2 border-blue-600 font-medium text-sm text-blue-600 dark:text-blue-400"
          >
            <span className="mr-2">🏠</span>
            Home
          </Link>
          <Link
            href="/journey"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">🗺️</span>
            My Journey
          </Link>
          <Link
            href="/practice"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">💪</span>
            Practice
          </Link>
          <Link
            href="/progress"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">📊</span>
            Progress
          </Link>
          <Link
            href="/adaptive"
            className="py-4 px-1 border-b-2 border-transparent text-green-600 hover:text-green-700 hover:border-green-300 dark:text-green-400 dark:hover:text-green-300 font-medium text-sm transition-colors relative"
          >
            <span className="mr-2">🤖</span>
            Start Onboarding
            {hasProfile && (
              <span className="absolute top-2 right-0 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            )}
          </Link>
        </div>
      </div>
    </nav>
  );
}

function ChatAgent() {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const Component = require('@/components/ChatAgent').default;
  return <Component />;
}

function DashboardView() {
  const [hasAdaptiveProfile, setHasAdaptiveProfile] = useState(false);

  useEffect(() => {
    // Check adaptive profile status
    const userId = SessionManager.getUserId();
    const onboardingStatus = SessionManager.getOnboardingStatus();
    setHasAdaptiveProfile(onboardingStatus === userId);
  }, []);

  return (
    <div className="space-y-6">
      {/* Adaptive Learning Showcase */}
      {!hasAdaptiveProfile ? (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-xl overflow-hidden">
          <div className="px-6 py-8 sm:p-10">
            <div className="text-center text-white">
              <div className="text-6xl mb-4 animate-bounce">🤖</div>
              <h2 className="text-3xl font-bold mb-3">
                Experience True Adaptive Learning
              </h2>
              <p className="text-xl text-blue-100 mb-6 max-w-2xl mx-auto">
                Let 8 AI agents collaborate to create a personalized learning journey just for you.
                Every decision is made by intelligent agents, not hardcoded rules.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 max-w-4xl mx-auto">
                <div className="bg-white/20 backdrop-blur rounded-lg p-4">
                  <div className="text-3xl mb-2">👁️</div>
                  <div className="font-semibold text-sm">Learner Profiler</div>
                  <div className="text-xs text-blue-100">Understands you</div>
                </div>
                <div className="bg-white/20 backdrop-blur rounded-lg p-4">
                  <div className="text-3xl mb-2">🗺️</div>
                  <div className="font-semibold text-sm">Journey Architect</div>
                  <div className="text-xs text-blue-100">Designs your path</div>
                </div>
                <div className="bg-white/20 backdrop-blur rounded-lg p-4">
                  <div className="text-3xl mb-2">📊</div>
                  <div className="font-semibold text-sm">Performance Analyzer</div>
                  <div className="text-xs text-blue-100">Tracks mastery</div>
                </div>
                <div className="bg-white/20 backdrop-blur rounded-lg p-4">
                  <div className="text-3xl mb-2">💡</div>
                  <div className="font-semibold text-sm">Recommendation Agent</div>
                  <div className="text-xs text-blue-100">Smart suggestions</div>
                </div>
              </div>

              <button
                onClick={() => window.location.href = '/adaptive'}
                className="px-8 py-4 bg-white text-blue-700 rounded-lg font-bold text-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-xl"
              >
                🚀 Start Your Adaptive Journey
              </button>

              <p className="text-sm text-blue-100 mt-4">
                ✨ Completely free • Takes 2 minutes • Remembers your progress
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg shadow-xl overflow-hidden">
          <div className="px-6 py-6 sm:p-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-5xl">🤖</div>
                <div className="text-white">
                  <h3 className="text-2xl font-bold mb-1">Your Adaptive Journey is Ready!</h3>
                  <p className="text-green-100">
                    8 AI agents have personalized a learning path just for you
                  </p>
                </div>
              </div>
              <button
                onClick={() => window.location.href = '/journey'}
                className="px-6 py-3 bg-white text-green-600 rounded-lg font-bold hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg flex items-center space-x-2"
              >
                <span>View Journey</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
