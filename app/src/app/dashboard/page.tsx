'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Header } from '@/components/layout/Header';
import NewsletterManager from '@/components/newsletter/NewsletterManager';
import { api, type User } from '@/lib/api';
// Define types and friendship levels locally
interface Friend {
  friendship_id: string;
  friend_name: string;
  friend_email: string;
  friendship_level: string;
  relationship_context?: string;
  last_interaction?: string;
  newsletter_subscribed: boolean;
}

interface TimelineItem {
  id: string;
  type: 'diary_entry' | 'life_fact';
  date: string;
  content: string;
  category?: string;
}

const friendshipLevels = {
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

function DashboardContent() {
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [stats] = useState({
    totalFriends: 2,
    monthlyInteractions: 15,
    profileViews: 28,
    newsletterSubscribers: 1
  });

  // Load user data and related info
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Get username from URL params (from onboarding) or localStorage
        const usernameFromUrl = searchParams.get('user');
        const usernameFromStorage = typeof window !== 'undefined' ? localStorage.getItem('currentUsername') : null;
        const currentUsername = usernameFromUrl || usernameFromStorage;
        
        if (!currentUsername) {
          setError('No authenticated user found. Please complete onboarding.');
          return;
        }
        
        // Store username for future use
        if (typeof window !== 'undefined' && usernameFromUrl) {
          localStorage.setItem('currentUsername', usernameFromUrl);
        }
        
        const userData = await api.getUser(currentUsername);
        if (userData) {
          setUser(userData);
          
          // Load friends and timeline data from real API
          try {
            const [friendsData, timelineData] = await Promise.all([
              api.getUserFriends(userData.user_id),
              api.getUserTimeline(userData.username)
            ]);
            setFriends(friendsData);
            setTimeline(timelineData);
          } catch (apiError) {
            console.warn('Failed to load some data, using empty arrays:', apiError);
            setFriends([]);
            setTimeline([]);
          }
        } else {
          setError('User not found');
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to load user data');
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, [searchParams]);

  // Add friend modal state
  const [isAddFriendOpen, setIsAddFriendOpen] = useState(false);
  const [newFriend, setNewFriend] = useState({
    name: '',
    email: '',
    level: 'good_friends',
    context: ''
  });

  // Content upload state
  const [newContent, setNewContent] = useState('');

  // Newsletter sending state
  const [isSendingNewsletter, setIsSendingNewsletter] = useState(false);
  const [newsletterSendResult, setNewsletterSendResult] = useState<string | null>(null);

  const handleLogout = () => {
    // Clear auth state and redirect
    if (typeof window !== 'undefined') {
      localStorage.removeItem('currentUsername');
    }
    window.location.href = '/';
  };

  const addFriend = () => {
    // In real app, call API to add friend
    console.log('Adding friend:', newFriend);
    setIsAddFriendOpen(false);
    setNewFriend({ name: '', email: '', level: 'good_friends', context: '' });
  };

  const uploadContent = async () => {
    if (!newContent.trim() || !user) return;
    
    try {
      const result = await api.uploadContent(user.user_id, newContent);
      console.log('Content uploaded successfully:', result);
      setNewContent('');
      
      // Refresh timeline data
      try {
        const timelineData = await api.getUserTimeline(user.username);
        setTimeline(timelineData);
      } catch (timelineError) {
        console.warn('Failed to refresh timeline after upload:', timelineError);
      }
    } catch (error) {
      console.error('Error uploading content:', error);
    }
  };

  const sendNewsletterNow = async () => {
    setIsSendingNewsletter(true);
    setNewsletterSendResult(null);
    
    try {
      // Use the actual backend endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/newsletter/admin/send-daily`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const result = await response.json();
        setNewsletterSendResult(`Newsletter sent successfully! Delivered to ${result.sent_count || 0} subscribers.`);
      } else {
        throw new Error('Failed to send newsletter');
      }
    } catch (error) {
      console.error('Newsletter send error:', error);
      setNewsletterSendResult('Failed to send newsletter. Please try again.');
    } finally {
      setIsSendingNewsletter(false);
      // Clear the message after 5 seconds
      setTimeout(() => setNewsletterSendResult(null), 5000);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
        <Header user={null} onLogout={handleLogout} />
        <div className="container mx-auto px-6 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading your dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
        <Header user={null} onLogout={handleLogout} />
        <div className="container mx-auto px-6 py-8 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || 'Failed to load user data'}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={() => window.location.reload()}>Retry</Button>
              {error?.includes('No authenticated user found') && (
                <Button variant="outline" onClick={() => window.location.href = '/onboarding'}>
                  Complete Onboarding
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <Header user={user} onLogout={handleLogout} />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-6xl mx-auto">
          
          {/* Header Section */}
          <div className="mb-8">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">
                  How you been, {user.full_name}?
                </h1>
                <p className="text-muted-foreground">
                  Manage your newsletter, share updates, and keep friends in the loop
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <Button 
                  size="lg"
                  className="px-6 py-3"
                  onClick={sendNewsletterNow}
                  disabled={isSendingNewsletter}
                >
                  {isSendingNewsletter ? '⏳ Sending...' : '📧 Send Newsletter Now'}
                </Button>
                {newsletterSendResult && (
                  <p className={`text-sm px-3 py-1 rounded ${
                    newsletterSendResult.includes('successfully') 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {newsletterSendResult}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Friends</p>
                    <p className="text-2xl font-bold text-foreground">{stats.totalFriends}</p>
                  </div>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <span className="text-primary">👥</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Newsletters Sent</p>
                    <p className="text-2xl font-bold text-foreground">{stats.monthlyInteractions}</p>
                  </div>
                  <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center">
                    <span className="text-secondary">📬</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Profile Views</p>
                    <p className="text-2xl font-bold text-foreground">{stats.profileViews}</p>
                  </div>
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                    <span className="text-accent">👁️</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Subscribers</p>
                    <p className="text-2xl font-bold text-foreground">{stats.newsletterSubscribers}</p>
                  </div>
                  <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
                    <span className="text-muted-foreground">📧</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Tabs */}
          <Tabs defaultValue="newsletter" className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="newsletter">Newsletter</TabsTrigger>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="friends">Friends</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

            {/* Newsletter Tab */}
            <TabsContent value="newsletter" className="space-y-6">
              <NewsletterManager userId={user?.user_id || ''} username={user?.username || ''} />
            </TabsContent>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              <div className="grid lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      Recent Activity
                      <Badge variant="outline">{timeline.length} updates</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {timeline.slice(0, 4).map((item) => (
                        <div key={item.id} className="border-l-2 border-primary pl-4">
                          <p className="text-sm font-medium text-foreground">
                            {item.content}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">
                              {item.type === 'diary_entry' ? 'Update' : 'Fact'}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {new Date(item.date).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Quick Upload</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      placeholder="Share an update about your life, achievements, or thoughts..."
                      value={newContent}
                      onChange={(e) => setNewContent(e.target.value)}
                      rows={4}
                    />
                    <Button onClick={uploadContent} disabled={!newContent.trim()}>
                      Upload Content
                    </Button>
                    <p className="text-xs text-muted-foreground">
                      Your AI will process this content and incorporate it into responses for friends.
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Your Profile</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium text-foreground">Share your profile</p>
                      <p className="text-sm text-muted-foreground">
                        Friends can chat with your AI at this URL
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="px-3 py-1 bg-background border rounded text-sm">
                        howyoubeen.com/{user?.username}
                      </code>
                      <Button size="sm" variant="outline">Copy</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Friends Tab */}
            <TabsContent value="friends" className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-semibold text-foreground">Friends</h2>
                <Dialog open={isAddFriendOpen} onOpenChange={setIsAddFriendOpen}>
                  <DialogTrigger asChild>
                    <Button>Add Friend</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add New Friend</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        label="Name"
                        placeholder="Friend's name"
                        value={newFriend.name}
                        onChange={(e) => setNewFriend({...newFriend, name: e.target.value})}
                      />
                      <Input
                        label="Email"
                        type="email"
                        placeholder="friend.email@example.com"
                        value={newFriend.email}
                        onChange={(e) => setNewFriend({...newFriend, email: e.target.value})}
                      />
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Friendship Level
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(friendshipLevels).map(([key, level]) => (
                            <button
                              key={key}
                              onClick={() => setNewFriend({...newFriend, level: key})}
                              className={`p-3 rounded-lg border text-left transition-colors ${
                                newFriend.level === key 
                                  ? 'border-primary bg-primary/10' 
                                  : 'border-border hover:bg-muted'
                              }`}
                            >
                              <p className="font-medium text-sm">{level.name}</p>
                              <p className="text-xs text-muted-foreground">{level.description}</p>
                            </button>
                          ))}
                        </div>
                      </div>
                      <Textarea
                        label="Relationship Context (Optional)"
                        placeholder="How do you know this person?"
                        value={newFriend.context}
                        onChange={(e) => setNewFriend({...newFriend, context: e.target.value})}
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <Button onClick={addFriend} className="flex-1">Add Friend</Button>
                        <Button variant="outline" onClick={() => setIsAddFriendOpen(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {friends.map((friend) => (
                  <Card key={friend.friendship_id}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="font-semibold text-foreground">{friend.friend_name}</h3>
                          <p className="text-sm text-muted-foreground">{friend.friend_email}</p>
                        </div>
                        <Badge style={{ backgroundColor: friendshipLevels[friend.friendship_level as keyof typeof friendshipLevels]?.color }}>
                          {friendshipLevels[friend.friendship_level as keyof typeof friendshipLevels]?.name}
                        </Badge>
                      </div>
                      
                      {friend.relationship_context && (
                        <p className="text-sm text-muted-foreground mb-3">
                          {friend.relationship_context}
                        </p>
                      )}
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>
                          Last interaction: {friend.last_interaction 
                            ? new Date(friend.last_interaction).toLocaleDateString()
                            : 'Never'
                          }
                        </span>
                        <div className="flex items-center gap-2">
                          {friend.newsletter_subscribed && (
                            <Badge variant="outline" className="text-xs">📧 Subscribed</Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Content Tab */}
            <TabsContent value="content" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Content Management</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-foreground mb-4">Upload New Content</h3>
                    <div className="space-y-4">
                      <Textarea
                        placeholder="Share updates, achievements, thoughts, or experiences..."
                        value={newContent}
                        onChange={(e) => setNewContent(e.target.value)}
                        rows={6}
                      />
                      <div className="flex gap-2">
                        <Button onClick={uploadContent} disabled={!newContent.trim()}>
                          Process with AI
                        </Button>
                        <Button variant="outline">Upload File</Button>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-foreground mb-4">Recent Content</h3>
                    <div className="space-y-3">
                      {timeline.map((item) => (
                        <div key={item.id} className="p-4 border border-border rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm text-foreground">{item.content}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="secondary" className="text-xs">
                                  {item.type === 'diary_entry' ? 'Update' : 'Fact'}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(item.date).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                            <Button variant="outline" size="sm">Edit</Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Profile Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <Input label="Full Name" value={user?.full_name || ''} readOnly />
                    <Input label="Username" value={user?.username || ''} readOnly />
                  </div>
                  <Input label="Email" value={user?.email || ''} readOnly />
                  <Textarea label="Bio" value={user?.bio || ''} rows={3} />
                  <Button>Update Profile</Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Privacy & Friendship Tiers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(friendshipLevels).map(([key, level]) => (
                      <div key={key} className="p-4 border border-border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-foreground">{level.name}</h4>
                          <Badge variant="outline">{key.replace('_', ' ')}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{level.description}</p>
                        <Button variant="outline" size="sm">Customize</Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

function DashboardPageFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <Header user={null} onLogout={() => {}} />
      <div className="container mx-auto px-6 py-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardPageFallback />}>
      <DashboardContent />
    </Suspense>
  );
}
