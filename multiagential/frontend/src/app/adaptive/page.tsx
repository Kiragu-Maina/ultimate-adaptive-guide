'use client';

import { useState, useEffect, useCallback } from 'react';
import OnboardingModal from '@/components/OnboardingModal';
import AdaptiveDashboard from '@/components/AdaptiveDashboard';
import { SessionManager } from '@/lib/session';
import { getApiUrl } from '@/lib/config';
import { useNotifications } from '@/lib/useNotifications';
import { notifyOnboardingComplete } from '@/lib/notifications';

interface LearnerProfile {
  overall_skill_level: string;
  priority_topics: string[];
  learning_pace: string;
  confidence: number;
  profile_summary: string;
}

interface LearningJourneyTopic {
  topic: string;
  position: number;
  status: string;
  estimated_hours: number;
  reasoning: string;
  is_milestone?: boolean;
  milestone_name?: string;
}

export default function AdaptivePage() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [learnerProfile, setLearnerProfile] = useState<LearnerProfile | null>(null);
  const [learningJourney, setLearningJourney] = useState<LearningJourneyTopic[]>([]);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [userId, setUserId] = useState<string>('');

  // Initialize notification system
  const { isSupported, permission, requestPermission } = useNotifications();

  const fetchProfile = useCallback(async (sessionUserId: string) => {
    try {
      const response = await fetch(`${getApiUrl()}/adaptive/performance`, {
        headers: {
          'x-user-key': sessionUserId,
        },
      });
      if (response.ok) {
        await response.json();
        // Extract profile info if available
        // For now, we'll set a placeholder
        setLearnerProfile({
          overall_skill_level: 'beginner',
          priority_topics: [],
          learning_pace: 'moderate',
          confidence: 90,
          profile_summary: 'Your adaptive learning profile'
        });
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  }, []);

  const checkOnboardingStatus = useCallback(async (sessionUserId: string) => {
    try {
      // Check if onboarding was completed (cookie-based)
      const onboardingUserId = SessionManager.getOnboardingStatus();

      if (onboardingUserId === sessionUserId) {
        // User has completed onboarding, fetch their journey
        const response = await fetch(`${getApiUrl()}/adaptive/journey`, {
          headers: {
            'x-user-key': sessionUserId,
          },
        });
        if (response.ok) {
          const data = await response.json();
          if (data.journey && data.journey.length > 0) {
            setLearningJourney(data.journey);
            setHasCompletedOnboarding(true);
            // Also fetch profile if available
            fetchProfile(sessionUserId);
            return;
          }
        }
      }

      // No onboarding found, show onboarding modal
      setShowOnboarding(true);
    } catch (error) {
      console.error('Error checking onboarding status:', error);
      setShowOnboarding(true);
    }
  }, [fetchProfile]);

  useEffect(() => {
    // Get or create user session
    const sessionUserId = SessionManager.getUserId();
    setUserId(sessionUserId);

    // Check if user has already completed onboarding
    checkOnboardingStatus(sessionUserId);
  }, [checkOnboardingStatus]);

  useEffect(() => {
    // Request notification permission if supported and not yet granted
    if (isSupported && permission === 'default') {
      requestPermission();
    }
  }, [isSupported, permission, requestPermission]);

  const handleOnboardingComplete = (profile: LearnerProfile, journey: LearningJourneyTopic[]) => {
    setLearnerProfile(profile);
    setLearningJourney(journey);
    setHasCompletedOnboarding(true);
    setShowOnboarding(false);

    // Mark onboarding as complete in cookies
    SessionManager.setOnboardingComplete(userId);

    // Show notification that learning journey is ready
    if (journey && journey.length > 0) {
      notifyOnboardingComplete(journey.length);
    }
  };

  const handleStartTopic = (topic: string) => {
    // Navigate to content page for this topic
    window.location.href = `/adaptive/content?topic=${encodeURIComponent(topic)}&user_id=${userId}`;
  };

  const handleRestartOnboarding = () => {
    // Clear onboarding status
    SessionManager.clearOnboarding();
    setShowOnboarding(true);
    setHasCompletedOnboarding(false);
    setLearnerProfile(null);
    setLearningJourney([]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Onboarding Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onComplete={handleOnboardingComplete}
      />

      {/* Main Content */}
      {!hasCompletedOnboarding && !showOnboarding ? (
        // Loading state
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin text-6xl mb-4">🤖</div>
            <p className="text-gray-600">Loading your adaptive learning experience...</p>
          </div>
        </div>
      ) : hasCompletedOnboarding ? (
        // Dashboard
        <>
          {/* Top Navigation */}
          <header className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-6">
                <div className="flex items-center">
                  <a href="/" className="text-3xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
                    AlkenaCode School
                  </a>
                  <span className="ml-3 px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                    AI-Powered Learning
                  </span>
                  <span className="ml-2 px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full">
                    🤖 Adaptive Mode Active
                  </span>
                </div>
                <button
                  onClick={handleRestartOnboarding}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm"
                >
                  ⚙️ Restart Onboarding
                </button>
              </div>
            </div>
          </header>

          <nav className="bg-white border-t border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex space-x-8">
                <a
                  href="/"
                  className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
                >
                  <span className="mr-2">🏠</span>
                  Home
                </a>
                <a
                  href="/journey"
                  className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
                >
                  <span className="mr-2">🗺️</span>
                  My Journey
                </a>
                <a
                  href="/practice"
                  className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
                >
                  <span className="mr-2">💪</span>
                  Practice
                </a>
                <a
                  href="/progress"
                  className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
                >
                  <span className="mr-2">📊</span>
                  Progress
                </a>
                <a
                  href="/adaptive"
                  className="py-4 px-1 border-b-2 border-green-600 text-green-600 font-medium text-sm transition-colors"
                >
                  <span className="mr-2">🤖</span>
                  Adaptive Learning
                </a>
              </div>
            </div>
          </nav>

          {/* Dashboard Content */}
          <AdaptiveDashboard
            profile={learnerProfile}
            journey={learningJourney}
            onStartTopic={handleStartTopic}
          />
        </>
      ) : null}

      {/* Welcome Screen (shown only when first visiting) */}
      {!hasCompletedOnboarding && !showOnboarding && (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
          <div className="max-w-2xl mx-auto text-center text-white p-8">
            <div className="text-6xl mb-6">🎓</div>
            <h1 className="text-5xl font-bold mb-4">Welcome to Adaptive Learning</h1>
            <p className="text-xl text-blue-100 mb-8">
              Experience truly personalized education powered by 8 AI agents working together to create your perfect learning journey.
            </p>
            <button
              onClick={() => setShowOnboarding(true)}
              className="px-8 py-4 bg-white text-blue-600 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors shadow-lg"
            >
              🚀 Start Your Journey
            </button>

            <div className="mt-12 grid grid-cols-2 gap-4 text-sm">
              <div className="bg-white/20 rounded-lg p-4">
                <div className="text-3xl mb-2">🤖</div>
                <div className="font-semibold">8 AI Agents</div>
                <div className="text-blue-100 text-xs mt-1">Working collaboratively</div>
              </div>
              <div className="bg-white/20 rounded-lg p-4">
                <div className="text-3xl mb-2">🎯</div>
                <div className="font-semibold">Personalized Path</div>
                <div className="text-blue-100 text-xs mt-1">Designed just for you</div>
              </div>
              <div className="bg-white/20 rounded-lg p-4">
                <div className="text-3xl mb-2">📊</div>
                <div className="font-semibold">Adaptive Difficulty</div>
                <div className="text-blue-100 text-xs mt-1">Matches your level</div>
              </div>
              <div className="bg-white/20 rounded-lg p-4">
                <div className="text-3xl mb-2">✨</div>
                <div className="font-semibold">Smart Recommendations</div>
                <div className="text-blue-100 text-xs mt-1">AI-powered suggestions</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
