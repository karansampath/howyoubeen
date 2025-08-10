/**
 * API client for HowYouBeen backend
 * Handles communication with FastAPI backend running on localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

class HowYouBeenAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
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
    const body: any = {
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
  async uploadFile(file: File, sessionId: string): Promise<{ file_id: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    return this.request<{ file_id: string; status: string }>('/api/onboarding/upload', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }
}

// Export singleton instance
export const api = new HowYouBeenAPI();

// Export types for use in components
export type { OnboardingSessionResponse, OnboardingDataRequest, OnboardingCompleteResponse, User, ChatResponse };