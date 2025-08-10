/**
 * Dummy data services for frontend development
 * Simulates backend API responses until backend routes are implemented
 */

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

export interface Friend {
  friendship_id: string;
  friend_name: string;
  friend_email: string;
  friendship_level: string;
  relationship_context?: string;
  last_interaction?: string;
  newsletter_subscribed: boolean;
}

export interface ChatMessage {
  id: string;
  message: string;
  response: string;
  timestamp: string;
  sender: 'friend' | 'ai';
}

export interface TimelineItem {
  id: string;
  type: 'diary_entry' | 'life_fact';
  date: string;
  content: string;
  category?: string;
}

// Dummy user data
export const dummyUsers: User[] = [
  {
    user_id: "user123",
    username: "johndoe",
    email: "john@example.com",
    full_name: "John Doe",
    bio: "Software engineer passionate about building meaningful connections. Love hiking, photography, and exploring new technologies.",
    profile_image_url: "/api/placeholder/150/150",
    is_public: true,
    onboarding_completed: true,
    created_at: "2024-01-15T10:00:00Z",
    knowledge_last_updated: "2024-03-15T15:30:00Z"
  }
];

// Dummy timeline data
export const dummyTimeline: TimelineItem[] = [
  {
    id: "tl1",
    type: "diary_entry",
    date: "2024-03-10T09:00:00Z",
    content: "Started learning React Native for a new mobile project. Excited about the possibilities for cross-platform development."
  },
  {
    id: "tl2", 
    type: "life_fact",
    date: "2024-03-05T14:20:00Z",
    content: "Completed a 5K marathon in under 25 minutes - personal best!",
    category: "fitness"
  },
  {
    id: "tl3",
    type: "diary_entry", 
    date: "2024-02-28T16:45:00Z",
    content: "Visited the new art museum downtown. The contemporary section was particularly inspiring."
  }
];

// Dummy friends data
export const dummyFriends: Friend[] = [
  {
    friendship_id: "f1",
    friend_name: "Sarah Johnson",
    friend_email: "sarah@example.com", 
    friendship_level: "best_friends",
    relationship_context: "College roommate",
    last_interaction: "2024-03-12T10:30:00Z",
    newsletter_subscribed: true
  },
  {
    friendship_id: "f2",
    friend_name: "Mike Chen",
    friend_email: "mike@example.com",
    friendship_level: "good_friends", 
    relationship_context: "Work colleague",
    last_interaction: "2024-03-08T14:15:00Z",
    newsletter_subscribed: false
  }
];

// Dummy chat data
export const dummyChatHistory: ChatMessage[] = [
  {
    id: "msg1",
    message: "Hey John! How have you been?",
    response: "Hi! I've been doing great, thanks for asking. Just finished a really exciting React Native project and have been keeping up with my running routine. How about you?",
    timestamp: "2024-03-12T10:30:00Z",
    sender: "friend"
  },
  {
    id: "msg2", 
    message: "Tell me about your recent projects",
    response: "I've been working on a cross-platform mobile app using React Native. It's been a great learning experience exploring the differences between iOS and Android development. The project involves real-time data synchronization which has been quite challenging but rewarding.",
    timestamp: "2024-03-12T10:35:00Z",
    sender: "friend"
  }
];

// API simulation functions
export const dummyAPI = {
  async getUser(username: string): Promise<User | null> {
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
    return dummyUsers.find(u => u.username === username) || null;
  },

  async getFriends(userId: string): Promise<Friend[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return dummyFriends;
  },

  async getTimeline(username: string, friendCode?: string): Promise<TimelineItem[]> {
    await new Promise(resolve => setTimeout(resolve, 400));
    return dummyTimeline;
  },

  async sendMessage(username: string, message: string, conversationId?: string): Promise<{
    response: string;
    conversation_id: string;
    suggested_questions: string[];
  }> {
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate AI thinking
    
    // Simple dummy AI responses
    const responses = [
      "That's a great question! Based on what I know about my recent activities, I'd say I've been focusing a lot on learning new technologies and staying active.",
      "I appreciate you asking! Things have been going well. I've been working on some exciting projects and maintaining a good work-life balance.",
      "Thanks for reaching out! I've been keeping busy with various personal and professional interests. What brings you here today?"
    ];
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    
    return {
      response: randomResponse,
      conversation_id: conversationId || `conv_${Date.now()}`,
      suggested_questions: [
        "What are you working on lately?",
        "How's your fitness routine going?", 
        "Any new hobbies or interests?"
      ]
    };
  },

  async startOnboarding(): Promise<{ session_id: string }> {
    await new Promise(resolve => setTimeout(resolve, 200));
    return { session_id: `session_${Date.now()}` };
  },

  async submitBasicInfo(sessionId: string, data: any): Promise<{ success: boolean }> {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { success: true };
  }
};

// Friendship levels with descriptions
export const friendshipLevels = {
  close_family: {
    name: "Close Family",
    description: "Immediate family members with access to personal details",
    color: "#8b5a3c"
  },
  best_friends: {
    name: "Best Friends", 
    description: "Closest friends who know about major life events and personal struggles",
    color: "#d97742"
  },
  good_friends: {
    name: "Good Friends",
    description: "Regular friends who stay updated on general life happenings",
    color: "#f4a462"
  },
  acquaintances: {
    name: "Acquaintances",
    description: "Colleagues and casual friends with basic updates only",
    color: "#e8956b"
  },
  public: {
    name: "Public",
    description: "Anyone can see this information",
    color: "#f5e6d8"
  }
};
