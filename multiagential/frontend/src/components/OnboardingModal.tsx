'use client';

import { useState, useEffect } from 'react';
import Modal from './Modal';
import { SessionManager } from '@/lib/session';
import { getApiUrl } from '@/lib/config';

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

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (profile: LearnerProfile, journey: LearningJourneyTopic[]) => void;
}

interface AgentActivity {
  agent: string;
  action: string;
  confidence?: string;
  reasoning?: string;
}

export default function OnboardingModal({ isOpen, onClose, onComplete }: OnboardingModalProps) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [agentActivity, setAgentActivity] = useState<AgentActivity[]>([]);
  const [userId, setUserId] = useState<string>('');

  // Form data
  const [interests, setInterests] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState('');
  const [learningGoals, setLearningGoals] = useState<string[]>([]);
  const [timeCommitment, setTimeCommitment] = useState(10);
  const [learningStyle, setLearningStyle] = useState('visual');
  const [skillLevel, setSkillLevel] = useState('beginner');
  const [background, setBackground] = useState('');

  useEffect(() => {
    // Get user session when modal opens
    if (isOpen) {
      const sessionUserId = SessionManager.getUserId();
      setUserId(sessionUserId);
    }
  }, [isOpen]);

  const interestOptions = [
    'Python Programming',
    'Web Development',
    'Machine Learning',
    'Data Science',
    'Mobile Development',
    'DevOps',
    'Cybersecurity',
    'Cloud Computing'
  ];

  const goalOptions = [
    { value: 'career_change', label: 'Career Change' },
    { value: 'skill_upgrade', label: 'Skill Upgrade' },
    { value: 'hobby', label: 'Personal Interest' },
    { value: 'certification', label: 'Get Certified' }
  ];

  const learningStyleOptions = [
    { value: 'visual', label: 'Visual (diagrams, videos)', icon: '👁️' },
    { value: 'reading', label: 'Reading (articles, docs)', icon: '📖' },
    { value: 'interactive', label: 'Interactive (hands-on)', icon: '💻' },
    { value: 'mixed', label: 'Mixed Approach', icon: '🔀' }
  ];

  const toggleInterest = (interest: string) => {
    setInterests(prev =>
      prev.includes(interest)
        ? prev.filter(i => i !== interest)
        : [...prev, interest]
    );
  };

  const addCustomInterest = () => {
    if (customInterest.trim() && !interests.includes(customInterest)) {
      setInterests([...interests, customInterest]);
      setCustomInterest('');
    }
  };

  const toggleGoal = (goal: string) => {
    setLearningGoals(prev =>
      prev.includes(goal)
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setAgentActivity([]);

    try {
      // Simulate agent activity updates
      setAgentActivity([
        { agent: 'Learner Profiler', action: 'Analyzing your interests and background...' }
      ]);

      const response = await fetch(`${getApiUrl()}/adaptive/onboarding`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-key': userId,
        },
        body: JSON.stringify({
          user_id: userId,
          interests,
          learning_goals: learningGoals,
          time_commitment: timeCommitment,
          learning_style: learningStyle,
          skill_level: skillLevel,
          background: background || undefined
        })
      });

      if (!response.ok) {
        throw new Error('Failed to complete onboarding');
      }

      const data = await response.json();

      // Show agent activity from backend
      if (data.agent_activity) {
        setAgentActivity(data.agent_activity);
      }

      // Wait a moment to show the agent activity
      setTimeout(() => {
        onComplete(data.learner_profile, data.learning_journey);
        setIsSubmitting(false);
      }, 1500);

    } catch (error) {
      console.error('Onboarding error:', error);
      alert('Failed to complete onboarding. Please try again.');
      setIsSubmitting(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1: return interests.length > 0;
      case 2: return learningGoals.length > 0;
      case 3: return true; // Always can proceed from preferences
      case 4: return true; // Review step
      default: return false;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="🎓 Start Your Adaptive Learning Journey">
      <div className="space-y-6">
        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-6">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                  s === step
                    ? 'bg-blue-500 text-white'
                    : s < step
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {s < step ? '✓' : s}
              </div>
              {s < 4 && (
                <div
                  className={`w-16 h-1 ${
                    s < step ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Agent Activity Display (when processing) */}
        {isSubmitting && agentActivity.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
              <span className="animate-spin mr-2">🤖</span>
              AI Agents Working...
            </h3>
            <div className="space-y-2">
              {agentActivity.map((activity, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-sm">
                  <span className="text-blue-600 font-medium">{activity.agent}:</span>
                  <span className="text-gray-700">{activity.action}</span>
                  {activity.confidence && (
                    <span className="text-green-600 ml-auto">({activity.confidence})</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 1: Interests */}
        {step === 1 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">What are you interested in learning?</h3>
            <p className="text-sm text-white mb-4">Select all that apply:</p>

            <div className="grid grid-cols-2 gap-2 mb-4">
              {interestOptions.map((interest) => (
                <button
                  key={interest}
                  onClick={() => toggleInterest(interest)}
                  className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                    interests.includes(interest)
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 bg-white text-black hover:border-blue-300'
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>

            <div className="flex space-x-2">
              <input
                type="text"
                value={customInterest}
                onChange={(e) => setCustomInterest(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addCustomInterest()}
                placeholder="Or add your own..."
                className="flex-1 p-2 border border-gray-300 rounded-lg text-sm text-black bg-white placeholder-gray-500"
              />
              <button
                onClick={addCustomInterest}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 font-medium"
              >
                Add
              </button>
            </div>

            {interests.length > 0 && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  ✓ Selected {interests.length} interest{interests.length !== 1 ? 's' : ''}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Learning Goals */}
        {step === 2 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">What are your learning goals?</h3>
            <p className="text-sm text-white mb-4">Select all that apply:</p>

            <div className="space-y-2">
              {goalOptions.map((goal) => (
                <button
                  key={goal.value}
                  onClick={() => toggleGoal(goal.value)}
                  className={`w-full p-4 rounded-lg border-2 text-left font-medium transition-colors ${
                    learningGoals.includes(goal.value)
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 bg-white text-black hover:border-blue-300'
                  }`}
                >
                  {goal.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Preferences */}
        {step === 3 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">Your Learning Preferences</h3>

            <div className="space-y-6">
              {/* Skill Level */}
              <div>
                <label className="block text-sm font-medium mb-2 text-white">Current Skill Level</label>
                <select
                  value={skillLevel}
                  onChange={(e) => setSkillLevel(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg text-black bg-white"
                >
                  <option value="beginner">Beginner - Just starting out</option>
                  <option value="intermediate">Intermediate - Some experience</option>
                  <option value="advanced">Advanced - Experienced</option>
                </select>
              </div>

              {/* Learning Style */}
              <div>
                <label className="block text-sm font-medium mb-2 text-white">Preferred Learning Style</label>
                <div className="grid grid-cols-2 gap-2">
                  {learningStyleOptions.map((style) => (
                    <button
                      key={style.value}
                      onClick={() => setLearningStyle(style.value)}
                      className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                        learningStyle === style.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 bg-white text-black hover:border-blue-300'
                      }`}
                    >
                      <div className="text-2xl mb-1">{style.icon}</div>
                      {style.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time Commitment */}
              <div>
                <label className="block text-sm font-medium mb-2 text-white">
                  Weekly Time Commitment: {timeCommitment} hours
                </label>
                <input
                  type="range"
                  min="1"
                  max="40"
                  value={timeCommitment}
                  onChange={(e) => setTimeCommitment(parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-white mt-1 font-medium">
                  <span>1 hr</span>
                  <span>20 hrs</span>
                  <span>40 hrs</span>
                </div>
              </div>

              {/* Background (optional) */}
              <div>
                <label className="block text-sm font-medium mb-2 text-white">
                  Background (Optional)
                </label>
                <textarea
                  value={background}
                  onChange={(e) => setBackground(e.target.value)}
                  placeholder="Tell us about your experience or what you hope to achieve..."
                  className="w-full p-2 border border-gray-300 rounded-lg text-sm text-black bg-white placeholder-gray-500"
                  rows={3}
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-white">Review Your Profile</h3>

            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2 text-black">Interests:</h4>
                <div className="flex flex-wrap gap-2">
                  {interests.map((interest) => (
                    <span key={interest} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                      {interest}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2 text-black">Goals:</h4>
                <div className="flex flex-wrap gap-2">
                  {learningGoals.map((goal) => (
                    <span key={goal} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                      {goalOptions.find(g => g.value === goal)?.label}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2 text-black">Skill Level:</h4>
                  <p className="text-sm capitalize text-black">{skillLevel}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2 text-black">Learning Style:</h4>
                  <p className="text-sm capitalize text-black">{learningStyle}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2 text-black">Time Commitment:</h4>
                <p className="text-sm text-black">{timeCommitment} hours per week</p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <p className="text-sm text-blue-900">
                  🤖 <strong>Our AI agents will analyze your profile</strong> to create a personalized learning journey just for you!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-4 border-t">
          {step > 1 && !isSubmitting && (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 text-white hover:bg-gray-700 rounded-lg font-medium"
            >
              ← Back
            </button>
          )}

          {step < 4 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!canProceed()}
              className={`ml-auto px-6 py-2 rounded-lg font-medium ${
                canProceed()
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className={`ml-auto px-6 py-2 rounded-lg font-medium ${
                isSubmitting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <span className="animate-spin mr-2">⚙️</span>
                  Creating Your Journey...
                </span>
              ) : (
                '🚀 Start Learning!'
              )}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
