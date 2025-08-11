/**
 * API client for HowYouBeen backend
 * Handles communication with FastAPI backend running on localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

// Auth related interfaces
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  expires_in: number;
}

export interface OnboardingSessionResponse {
  session_id: string;
  current_step: number;
  status: string;
}

export interface OnboardingDataRequest {
  username: string;
  email: string;
  bio: string;
  data_sources: string[];
  visibility_preference: string;
}

export interface OnboardingCompleteResponse {
  user_id: string;
  username: string;
  profile_url: string;
  status: string;
}

export interface User {
  user_id: string;
  username: string;
  email: string;
  full_name: string;
  bio?: string;
  profile_image_url?: string;
  is_public: boolean;
  onboarding_completed: boolean;
  created_at: string;
  knowledge_last_updated: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  suggested_questions: string[];
}

export interface LifeEventRequest {
  user_id: string;
  summary: string;
  start_date?: string;
  end_date?: string;
  visibility?: string;
  associated_docs?: string[];
}

export interface LifeEventResponse {
  event_id: string;
  user_id: string;
  summary: string;
  start_date: string;
  end_date?: string;
  visibility: string;
  associated_docs: string[];
  created_at: string;
  updated_at: string;
}

export interface LifeFactRequest {
  user_id: string;
  summary: string;
  category?: string;
  visibility?: string;
  associated_docs?: string[];
}

export interface LifeFactResponse {
  fact_id: string;
  user_id: string;
  summary: string;
  category?: string;
  visibility: string;
  associated_docs: string[];
  created_at: string;
  updated_at: string;
}

export interface NewsletterConfigRequest {
  user_id: string;
  name: string;
  description?: string;
  frequency?: string;
  privacy_level?: string;
  is_active?: boolean;
}

export interface NewsletterConfigResponse {
  config_id: string;
  user_id: string;
  name: string;
  description?: string;
  frequency: string;
  privacy_level: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatQuestionRequest {
  user_id: string;
  question: string;
  conversation_history?: ChatMessage[];
  max_tokens?: number;
}

export interface ChatQuestionResponse {
  response: string;
  conversation_id: string;
  suggested_questions: string[];
}

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

class HowYouBeenAPI {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.authToken = localStorage.getItem('auth_token');
    }
  }

  // Set authentication token
  setAuthToken(token: string | null) {
    this.authToken = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  }

  // Get current auth token
  getAuthToken(): string | null {
    return this.authToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    // Add authorization header if token is available
    if (this.authToken) {
      headers.Authorization = `Bearer ${this.authToken}`;
    }
    
    const config: RequestInit = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new APIError(response.status, errorText || response.statusText);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as unknown as T;
      }
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Onboarding API endpoints
  async startOnboarding(): Promise<OnboardingSessionResponse> {
    return this.request<OnboardingSessionResponse>('/api/onboarding/start', {
      method: 'POST',
    });
  }

  async submitOnboardingData(
    sessionId: string,
    data: OnboardingDataRequest
  ): Promise<OnboardingCompleteResponse> {
    return this.request<OnboardingCompleteResponse>('/api/onboarding/complete', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        ...data,
      }),
    });
  }

  // User profile API endpoints
  async getUser(username: string): Promise<User | null> {
    try {
      return await this.request<User>(`/api/users/${username}`);
    } catch (error) {
      if (error instanceof APIError && error.status === 404) {
        return null;
      }
      throw error;
    }
  }

  // Chat API endpoints
  async sendMessage(
    username: string,
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    const body: { message: string; conversation_id?: string } = {
      message,
    };

    if (conversationId) {
      body.conversation_id = conversationId;
    }

    return this.request<ChatResponse>(`/api/chat/${username}`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }

  // File upload (for data sources)
  async uploadFile(file: File, sessionId: string, description?: string): Promise<{ success: boolean; document_id: string; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    formData.append('description', description || '');

    return this.request<{ success: boolean; document_id: string; message: string }>('/api/onboarding/upload-document', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  // Newsletter API endpoints
  async getSubscriptionInfo(linkCode: string): Promise<{ username: string; privacy_level: string; available_frequencies: string[] }> {
    return this.request<{ username: string; privacy_level: string; available_frequencies: string[] }>(`/api/newsletter/link/${linkCode}`);
  }

  async subscribeToNewsletter(payload: {
    privacy_code: string;
    subscriber_email: string;
    frequency: string;
    subscriber_name?: string;
    referral_code?: string;
  }): Promise<{ success: boolean; subscription_id: string; message: string; unsubscribe_code: string }> {
    return this.request<{ success: boolean; subscription_id: string; message: string; unsubscribe_code: string }>('/api/newsletter/subscribe', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async createSubscriptionLink(userId: string, privacyLevel: string): Promise<{ link: string }> {
    return this.request<{ link: string }>(`/api/newsletter/create-link?user_id=${userId}&privacy_level=${privacyLevel}`, {
      method: 'POST',
    });
  }

  async getUserSubscriptions(userId: string): Promise<{ subscriptions: any[]; total_count: number }> {
    return this.request<{ subscriptions: any[]; total_count: number }>(`/api/newsletter/subscriptions/${userId}`);
  }

  // Referral Link API endpoints
  async createReferralLink(payload: {
    user_id: string;
    created_by_user_id: string;
    friend_name: string;
    friend_email?: string;
    privacy_level: string;
    expires_at?: string;
  }): Promise<{ success: boolean; referral_link: string; referral_code: string; message: string }> {
    return this.request<{ success: boolean; referral_link: string; referral_code: string; message: string }>('/api/newsletter/create-referral-link', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getUserReferralLinks(createdByUserId: string): Promise<{ success: boolean; referral_links: any[]; total_count: number }> {
    return this.request<{ success: boolean; referral_links: any[]; total_count: number }>(`/api/newsletter/referral-links/${createdByUserId}`);
  }

  async getUserReferrals(userId: string): Promise<{ success: boolean; referrals: any[]; total_count: number }> {
    return this.request<{ success: boolean; referrals: any[]; total_count: number }>(`/api/newsletter/referrals/${userId}`);
  }

  // Newsletter generation API endpoints
  async generateNewsletter(payload: {
    user_id: string;
    newsletter_config: {
      instructions?: string;
      periodicity?: number;
      start_date?: string;
      visibility: Array<{
        type: string;
        name?: string;
      }>;
      name?: string;
    };
  }): Promise<{
    success: boolean;
    content?: string;
    error_message?: string;
    events_count: number;
    generation_summary: any;
  }> {
    return this.request<{
      success: boolean;
      content?: string;
      error_message?: string;
      events_count: number;
      generation_summary: any;
    }>('/api/newsletter/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Life Events API endpoints
  async createLifeEvent(data: LifeEventRequest): Promise<LifeEventResponse> {
    return this.request<LifeEventResponse>('/api/content/life-events', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUserLifeEvents(userId: string, limit: number = 50, offset: number = 0): Promise<LifeEventResponse[]> {
    return this.request<LifeEventResponse[]>(`/api/content/life-events/${userId}?limit=${limit}&offset=${offset}`);
  }

  async getLifeEventsByDateRange(
    userId: string,
    startDate: string,
    endDate: string,
    visibilityLevels?: string[]
  ): Promise<LifeEventResponse[]> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    });
    
    if (visibilityLevels && visibilityLevels.length > 0) {
      params.append('visibility_levels', visibilityLevels.join(','));
    }

    return this.request<LifeEventResponse[]>(`/api/content/life-events/${userId}/date-range?${params}`);
  }

  // Life Facts API endpoints
  async createLifeFact(data: LifeFactRequest): Promise<LifeFactResponse> {
    return this.request<LifeFactResponse>('/api/content/life-facts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUserLifeFacts(userId: string, category?: string): Promise<LifeFactResponse[]> {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request<LifeFactResponse[]>(`/api/content/life-facts/${userId}${params}`);
  }

  // Newsletter Configuration API endpoints
  async createNewsletterConfig(data: NewsletterConfigRequest): Promise<NewsletterConfigResponse> {
    return this.request<NewsletterConfigResponse>('/api/content/newsletter-configs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUserNewsletterConfigs(userId: string): Promise<NewsletterConfigResponse[]> {
    return this.request<NewsletterConfigResponse[]>(`/api/content/newsletter-configs/${userId}`);
  }

  // Search and Activity API endpoints
  async searchUserContent(userId: string, query: string, contentTypes?: string[]): Promise<{
    life_events?: LifeEventResponse[];
    life_facts?: LifeFactResponse[];
    documents?: any[];
  }> {
    const params = new URLSearchParams({ query });
    
    if (contentTypes && contentTypes.length > 0) {
      params.append('content_types', contentTypes.join(','));
    }

    return this.request<any>(`/api/content/search/${userId}?${params}`);
  }

  async getUserActivitySummary(userId: string, days: number = 30): Promise<{
    user_id: string;
    days: number;
    activity_counts: {
      life_events: number;
      life_facts: number;
      documents: number;
      total: number;
    };
    recent_items: {
      life_events: LifeEventResponse[];
      life_facts: LifeFactResponse[];
      documents: any[];
    };
    total_counts: {
      life_events: number;
      life_facts: number;
      documents: number;
    };
  }> {
    return this.request<any>(`/api/content/activity-summary/${userId}?days=${days}`);
  }

  // AI Chat/Question API endpoint
  async askQuestion(data: ChatQuestionRequest): Promise<ChatQuestionResponse> {
    return this.request<ChatQuestionResponse>('/api/content/question', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Friends and timeline API endpoints
  async getUserFriends(userId: string): Promise<any[]> {
    return this.request<any[]>(`/api/users/${userId}/friends`);
  }

  async getUserTimeline(username: string): Promise<any[]> {
    return this.request<any[]>(`/api/users/${username}/timeline`);
  }

  async uploadContent(userId: string, content: string): Promise<{ success: boolean; message: string; entry_id: string }> {
    return this.request<{ success: boolean; message: string; entry_id: string }>(`/api/users/${userId}/content`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // Authentication API endpoints
  async login(request: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    
    // Store token after successful login
    this.setAuthToken(response.token);
    
    return response;
  }

  async register(request: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    
    // Store token after successful registration
    this.setAuthToken(response.token);
    
    return response;
  }

  async getCurrentUser(): Promise<{ user: User }> {
    return this.request<{ user: User }>('/api/auth/me');
  }

  async logout(): Promise<{ message: string }> {
    try {
      const response = await this.request<{ message: string }>('/api/auth/logout', {
        method: 'POST',
      });
      
      // Clear token after logout
      this.setAuthToken(null);
      
      return response;
    } catch (error) {
      // Clear token even if logout request fails
      this.setAuthToken(null);
      throw error;
    }
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/refresh', {
      method: 'POST',
    });
    
    // Update stored token
    this.setAuthToken(response.token);
    
    return response;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  // Data source connection endpoints
  async connectGitHub(sessionId: string, username: string, githubToken?: string): Promise<{
    success: boolean;
    platform: string;
    message: string;
    summary?: any;
  }> {
    return this.request('/api/onboarding/connect-github', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        username,
        github_token: githubToken
      }),
    });
  }

  async connectWebsite(sessionId: string, url: string): Promise<{
    success: boolean;
    platform: string;
    message: string;
    summary?: any;
  }> {
    return this.request('/api/onboarding/connect-website', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        url
      }),
    });
  }
}

// Export singleton instance
export const api = new HowYouBeenAPI();