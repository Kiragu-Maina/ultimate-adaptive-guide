/**
 * Web Push Notification Utility
 * Handles browser notifications that work even when user is on another tab/app
 */

export interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: Record<string, unknown>;
  requireInteraction?: boolean;
}

class NotificationManager {
  private static instance: NotificationManager;
  private permissionGranted: boolean = false;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;

  private constructor() {
    this.checkPermission();
  }

  static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }

  /**
   * Check if notifications are supported and permission status
   */
  private checkPermission(): void {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      this.permissionGranted = Notification.permission === 'granted';
    }
  }

  /**
   * Request permission for notifications
   */
  async requestPermission(): Promise<boolean> {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      this.permissionGranted = true;
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.permissionGranted = permission === 'granted';
      return this.permissionGranted;
    }

    return false;
  }

  /**
   * Register service worker for background notifications
   */
  async registerServiceWorker(): Promise<void> {
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
      return;
    }

    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        this.serviceWorkerRegistration = registration;
        console.log('Service Worker registered:', registration);
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  /**
   * Show notification
   */
  async showNotification(options: NotificationOptions): Promise<void> {
    if (!this.permissionGranted) {
      const granted = await this.requestPermission();
      if (!granted) {
        console.warn('Notification permission not granted');
        return;
      }
    }

    const defaultOptions = {
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      vibrate: [200, 100, 200],
      requireInteraction: true,
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1,
        url: window.location.origin,
      },
    };

    const notificationOptions = {
      ...defaultOptions,
      ...options,
      data: {
        ...defaultOptions.data,
        ...options.data,
      },
    };

    try {
      // Try using service worker first for better persistence
      if (this.serviceWorkerRegistration) {
        await this.serviceWorkerRegistration.showNotification(
          options.title,
          notificationOptions
        );
      } else {
        // Fallback to standard notification
        const notification = new Notification(options.title, notificationOptions);

        // Auto-focus window when clicked
        notification.onclick = (event) => {
          event.preventDefault();
          window.focus();
          if (options.data?.url && typeof options.data.url === 'string') {
            window.location.href = options.data.url;
          }
          notification.close();
        };
      }
    } catch (error) {
      console.error('Failed to show notification:', error);
    }
  }

  /**
   * Predefined notifications for common scenarios
   */

  /**
   * Notification when onboarding completes
   */
  async notifyOnboardingComplete(journeyTopics: number): Promise<void> {
    await this.showNotification({
      title: 'Your Learning Journey is Ready!',
      body: `We've created a personalized syllabus with ${journeyTopics} topics tailored just for you. Click to start learning!`,
      tag: 'onboarding-complete',
      data: {
        url: `${window.location.origin}/journey`,
        type: 'onboarding',
      },
      requireInteraction: true,
    });
  }

  /**
   * Notification when content generation completes
   */
  async notifyContentReady(topic: string): Promise<void> {
    await this.showNotification({
      title: 'Your Content is Ready!',
      body: `AI agents have finished creating personalized content for "${topic}". Click to start learning!`,
      tag: 'content-ready',
      data: {
        url: `${window.location.origin}/adaptive/content?topic=${encodeURIComponent(topic)}`,
        type: 'content',
        topic,
      },
      requireInteraction: true,
    });
  }

  /**
   * Notification for quiz results
   */
  async notifyQuizComplete(topic: string, score: number): Promise<void> {
    const emoji = score >= 70 ? '🎉' : '💪';
    const message = score >= 70
      ? `Great job! You scored ${score}% on "${topic}"`
      : `You scored ${score}% on "${topic}". Keep practicing!`;

    await this.showNotification({
      title: `${emoji} Quiz Complete`,
      body: message,
      tag: 'quiz-complete',
      data: {
        url: `${window.location.origin}/progress`,
        type: 'quiz',
        topic,
        score,
      },
    });
  }

  /**
   * Notification for milestone completion
   */
  async notifyMilestoneComplete(milestone: string): Promise<void> {
    await this.showNotification({
      title: 'Milestone Completed!',
      body: `Congratulations! You've completed "${milestone}". Check your progress!`,
      tag: 'milestone-complete',
      data: {
        url: `${window.location.origin}/progress`,
        type: 'milestone',
        milestone,
      },
    });
  }

  /**
   * Check if notifications are supported
   */
  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof navigator !== 'undefined' &&
      'Notification' in window &&
      'serviceWorker' in navigator
    );
  }

  /**
   * Get current permission status
   */
  getPermissionStatus(): NotificationPermission {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      return Notification.permission;
    }
    return 'default';
  }
}

// Export singleton instance
export const notificationManager = NotificationManager.getInstance();

// Convenience functions
export const requestNotificationPermission = () =>
  notificationManager.requestPermission();

export const showNotification = (options: NotificationOptions) =>
  notificationManager.showNotification(options);

export const notifyOnboardingComplete = (journeyTopics: number) =>
  notificationManager.notifyOnboardingComplete(journeyTopics);

export const notifyContentReady = (topic: string) =>
  notificationManager.notifyContentReady(topic);

export const notifyQuizComplete = (topic: string, score: number) =>
  notificationManager.notifyQuizComplete(topic, score);

export const notifyMilestoneComplete = (milestone: string) =>
  notificationManager.notifyMilestoneComplete(milestone);

export const isNotificationSupported = () =>
  notificationManager.isSupported();

export const getNotificationPermission = () =>
  notificationManager.getPermissionStatus();
