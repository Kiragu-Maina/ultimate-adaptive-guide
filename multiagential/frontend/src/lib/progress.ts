export interface LearningStats {
  quizzesCompleted: number;
  topicsExplored: number;
  feedbackReceived: number;
}

export class ProgressTracker {
  private static STATS_KEY = 'learningStats';
  private static ACTIVITY_KEY = 'recentActivity';
  private static MAX_ACTIVITIES = 20;

  static getStats(): LearningStats {
    if (typeof window === 'undefined') {
      return { quizzesCompleted: 0, topicsExplored: 0, feedbackReceived: 0 };
    }
    
    const stored = localStorage.getItem(this.STATS_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return { quizzesCompleted: 0, topicsExplored: 0, feedbackReceived: 0 };
  }

  static updateStats(updates: Partial<LearningStats>) {
    if (typeof window === 'undefined') return;
    
    const current = this.getStats();
    const updated = { ...current, ...updates };
    localStorage.setItem(this.STATS_KEY, JSON.stringify(updated));
  }

  static incrementQuizCount() {
    const current = this.getStats();
    this.updateStats({ quizzesCompleted: current.quizzesCompleted + 1 });
  }

  static incrementTopicCount() {
    const current = this.getStats();
    this.updateStats({ topicsExplored: current.topicsExplored + 1 });
  }

  static incrementFeedbackCount() {
    const current = this.getStats();
    this.updateStats({ feedbackReceived: current.feedbackReceived + 1 });
  }

  static getRecentActivity(): string[] {
    if (typeof window === 'undefined') return [];
    
    const stored = localStorage.getItem(this.ACTIVITY_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return [];
  }

  static addActivity(activity: string) {
    if (typeof window === 'undefined') return;
    
    const current = this.getRecentActivity();
    const timestamp = new Date().toLocaleString();
    const newActivity = `${timestamp}: ${activity}`;
    
    const updated = [newActivity, ...current].slice(0, this.MAX_ACTIVITIES);
    localStorage.setItem(this.ACTIVITY_KEY, JSON.stringify(updated));
  }

  static logQuizCompletion(topic: string, score: number, total: number) {
    this.incrementQuizCount();
    const percentage = Math.round((score / total) * 100);
    this.addActivity(`Completed quiz on "${topic}" - ${score}/${total} (${percentage}%)`);
  }

  static logContentExploration(topic: string) {
    this.incrementTopicCount();
    this.addActivity(`Explored content on "${topic}"`);
  }

  static logFeedbackSession(preview: string) {
    this.incrementFeedbackCount();
    const shortPreview = preview.length > 50 ? preview.substring(0, 50) + '...' : preview;
    this.addActivity(`Received feedback about "${shortPreview}"`);
  }

  static logCourseEnrollment(courseTitle: string) {
    this.addActivity(`Enrolled in course: "${courseTitle}"`);
  }

  static logModuleCompletion(courseTitle: string, moduleTitle: string) {
    this.addActivity(`Completed module: "${moduleTitle}" in ${courseTitle}`);
  }
}