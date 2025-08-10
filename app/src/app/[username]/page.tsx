'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { api, type User, type ChatResponse } from '@/lib/api';

interface Message {
  id: string;
  content: string;
  sender: 'friend' | 'ai';
  timestamp: Date;
}

interface Props {
  params: Promise<{
    username: string;
  }>;
}

export default function FriendChatPage({ params }: Props) {
  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadUserProfile = useCallback(async () => {
    try {
      const resolvedParams = await params;
      const userData = await api.getUser(resolvedParams.username);
      if (userData) {
        setUser(userData);
        // Send welcome message
        const welcomeMessage: Message = {
          id: 'welcome',
          content: `Hi! I'm ${userData.full_name || userData.username}'s AI assistant. I can help you stay updated on what's happening in their life. What would you like to know?`,
          sender: 'ai',
          timestamp: new Date()
        };
        setMessages([welcomeMessage]);
        setSuggestedQuestions([
          `What has ${userData.full_name || userData.username} been up to lately?`,
          'Tell me about recent projects',
          'How are things going?'
        ]);
      } else {
        setError('User not found');
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
      setError(error instanceof Error ? error.message : 'Failed to load user profile');
    }
  }, [params]);

  useEffect(() => {
    loadUserProfile();
  }, [loadUserProfile]);

  const sendMessage = async (messageText?: string) => {
    const text = messageText || currentMessage.trim();
    if (!text || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: text,
      sender: 'friend',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      // Get AI response
      const resolvedParams = await params;
      const response = await api.sendMessage(resolvedParams.username, text, conversationId || undefined);
      
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'ai',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setSuggestedQuestions(response.suggested_questions);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I had trouble processing that. Could you try again?',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <h1 className="text-2xl font-bold text-foreground mb-4">Profile Not Found</h1>
            <p className="text-muted-foreground mb-6">
              {error}
            </p>
            <Button onClick={() => window.location.href = '/'}>
              Go Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <div className="container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          
          {/* Profile Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <div className="text-center">
                  <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl text-primary-foreground">
                      {(user.full_name || user.username).charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <CardTitle className="text-xl">{user.full_name || user.username}</CardTitle>
                  <p className="text-muted-foreground">@{user.username}</p>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">{user.bio}</p>
                <div className="text-xs text-muted-foreground">
                  Last updated: {new Date(user.knowledge_last_updated).toLocaleDateString()}
                </div>
              </CardContent>
            </Card>

            {/* Profile Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Profile Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-sm text-foreground">AI Assistant Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-sm text-foreground">
                      {user.is_public ? 'Public Profile' : 'Private Profile'}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-3">
                    Profile created: {new Date(user.created_at).toLocaleDateString()}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Newsletter Signup */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Stay Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Get email updates about {user.full_name || user.username}&apos;s latest activities
                </p>
                <Button variant="outline" className="w-full">
                  Subscribe to Newsletter
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <Card className="h-[600px] flex flex-col">
              <CardHeader className="border-b">
                <CardTitle className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  Chat with {user.full_name || user.username}&apos;s AI
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Ask me anything about {user.full_name || user.username}&apos;s life and activities
                </p>
              </CardHeader>

              {/* Messages */}
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'friend' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg ${
                        message.sender === 'friend'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-foreground'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted text-foreground p-3 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </CardContent>

              {/* Suggested Questions */}
              {suggestedQuestions.length > 0 && (
                <div className="px-4 pb-2">
                  <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
                  <div className="flex flex-wrap gap-2">
                    {suggestedQuestions.map((question, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => sendMessage(question)}
                        disabled={isLoading}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    placeholder={`Message ${user.full_name || user.username}&apos;s AI...`}
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  <Button 
                    onClick={() => sendMessage()}
                    disabled={!currentMessage.trim() || isLoading}
                  >
                    Send
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
