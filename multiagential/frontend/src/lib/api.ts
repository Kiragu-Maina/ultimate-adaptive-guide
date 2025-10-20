interface QuizQuestion {
  question: string;
  options: string[];
}

interface Quiz {
  quiz_id: string;
  questions: QuizQuestion[];
}

interface QuizSubmission {
  quiz_id: string;
  answers: string[];
}

interface QuizResult {
  score: number;
  total: number;
}

interface FeedbackRequest {
  user_input: string;
}

interface FeedbackResponse {
  feedback: string;
}

interface ContentItem {
  title: string;
  href: string;
  body: string;
}

interface Resource {
  title: string;
  url: string;
  type: 'pdf' | 'web';
}

interface ContentResponse {
  content: string;
  exercises: string[];
  resources: Resource[];
  diagram: string;
}

interface ProgressResponse {
  current_topic: string;
}

interface CourseEnrollment {
  course_id: string;
  enrolled_at: string;
  last_accessed: string;
  last_module_id: string | null;
}

interface CourseEnrollmentRequest {
  course_id: string;
}

interface ModuleProgressRequest {
  course_id: string;
  module_id: string;
  completed: boolean;
}

interface CourseAccessRequest {
  course_id: string;
  module_id?: string;
}

interface CourseProgress {
  course_id: string;
  progress: Record<string, boolean>;
}

interface CourseSummary {
  summary: {
    total_enrollments: number;
    completed_modules: number;
    recent_course_id: string | null;
    recent_module_id: string | null;
  };
  recent_courses: CourseEnrollment[];
}

class ApiClient {
  private baseUrl: string;
  private userKey: string | null = null;

  constructor(baseUrl?: string) {
    // Read from environment variable, fallback to parameter or default
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4465';
    this.userKey = this.getUserKey();
  }

  private getUserKey(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('userKey');
  }

  private setUserKey(key: string) {
    if (typeof window === 'undefined') return;
    this.userKey = key;
    localStorage.setItem('userKey', key);
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.userKey) {
      headers['x-user-key'] = this.userKey;
    }
    
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const userKey = response.headers.get('X-User-Key');
    if (userKey && userKey !== this.userKey) {
      this.setUserKey(userKey);
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getQuiz(topic?: string, numQuestions: number = 2): Promise<Quiz> {
    const params = new URLSearchParams();
    if (topic) params.append('topic', topic);
    params.append('num_questions', numQuestions.toString());

    const response = await fetch(`${this.baseUrl}/quiz?${params.toString()}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<Quiz>(response);
  }

  async submitQuiz(submission: QuizSubmission): Promise<QuizResult> {
    const response = await fetch(`${this.baseUrl}/quiz/submit`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(submission),
    });

    return this.handleResponse<QuizResult>(response);
  }

  async getFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await fetch(`${this.baseUrl}/feedback`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<FeedbackResponse>(response);
  }

  async getContent(topic?: string): Promise<ContentResponse> {
    const params = new URLSearchParams();
    if (topic) params.append('topic', topic);

    const response = await fetch(`${this.baseUrl}/content?${params.toString()}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<ContentResponse>(response);
  }

  async getProgress(): Promise<ProgressResponse> {
    const response = await fetch(`${this.baseUrl}/progress`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<ProgressResponse>(response);
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/`, {
      method: 'GET',
    });

    return this.handleResponse<{ status: string }>(response);
  }

  // Course Management Methods
  async enrollInCourse(courseId: string): Promise<{ message: string; course_id: string }> {
    const response = await fetch(`${this.baseUrl}/courses/enroll`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ course_id: courseId }),
    });

    return this.handleResponse<{ message: string; course_id: string }>(response);
  }

  async updateCourseAccess(courseId: string, moduleId?: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/courses/access`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ course_id: courseId, module_id: moduleId }),
    });

    return this.handleResponse<{ message: string }>(response);
  }

  async getUserEnrollments(): Promise<{ enrollments: CourseEnrollment[] }> {
    const response = await fetch(`${this.baseUrl}/courses/enrollments`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<{ enrollments: CourseEnrollment[] }>(response);
  }

  async updateModuleProgress(courseId: string, moduleId: string, completed: boolean): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/courses/module-progress`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ course_id: courseId, module_id: moduleId, completed }),
    });

    return this.handleResponse<{ message: string }>(response);
  }

  async getCourseProgress(courseId: string): Promise<CourseProgress> {
    const response = await fetch(`${this.baseUrl}/courses/${courseId}/progress`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<CourseProgress>(response);
  }

  async getCourseSummary(): Promise<CourseSummary> {
    const response = await fetch(`${this.baseUrl}/courses/summary`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<CourseSummary>(response);
  }
}

export const api = new ApiClient();
export type { 
  Quiz, 
  QuizQuestion, 
  QuizSubmission, 
  QuizResult, 
  FeedbackRequest, 
  FeedbackResponse, 
  ContentItem, 
  Resource,
  ContentResponse, 
  ProgressResponse, 
  CourseEnrollment, 
  CourseEnrollmentRequest, 
  ModuleProgressRequest, 
  CourseAccessRequest, 
  CourseProgress, 
  CourseSummary 
};