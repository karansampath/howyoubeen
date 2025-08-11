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
import { AuthenticatedHeader } from '@/components/layout/AuthenticatedHeader';
import NewsletterManager from '@/components/newsletter/NewsletterManager';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/components/auth/AuthContext';
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
  const { user: authUser, logout } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [subscriberCount, setSubscriberCount] = useState(0);

  // Load user data and related info
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Use authenticated user data directly
        if (!authUser) {
          setError('No authenticated user found. Please login.');
          return;
        }
        
        const currentUser: User | null = authUser;
        setUser(currentUser);
        
        if (currentUser) {
          
          // Load friends, timeline, subscription, life events, and life facts data from real API
          try {
            const [friendsData, timelineData, subscriptionsData, lifeEventsData, lifeFactsData] = await Promise.all([
              api.getUserFriends(currentUser.user_id),
              api.getUserTimeline(currentUser.username),
              api.getUserSubscriptions(currentUser.user_id).catch(() => ({ subscriptions: [] })),
              api.getUserLifeEvents(currentUser.user_id).catch(() => []),
              api.getUserLifeFacts(currentUser.user_id).catch(() => [])
            ]);
            setFriends(friendsData);
            setTimeline(timelineData);
            setSubscriberCount(subscriptionsData.subscriptions?.length || 0);
            setLifeEvents(lifeEventsData);
            setLifeFacts(lifeFactsData);
          } catch (apiError) {
            console.warn('Failed to load some data, using empty arrays:', apiError);
            setFriends([]);
            setTimeline([]);
            setSubscriberCount(0);
            setLifeEvents([]);
            setLifeFacts([]);
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
  }, [searchParams, authUser]);

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

  // Newsletter generation and sending state
  const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
  const [isSendingNewsletter, setIsSendingNewsletter] = useState(false);
  const [generatedNewsletter, setGeneratedNewsletter] = useState<string | null>(null);
  const [newsletterGenerationResult, setNewsletterGenerationResult] = useState<string | null>(null);
  const [newsletterSendResult, setNewsletterSendResult] = useState<string | null>(null);
  const [lifeEvents, setLifeEvents] = useState<any[]>([]);
  const [lifeFacts, setLifeFacts] = useState<any[]>([]);

  // Data source connection state
  const [isGitHubDialogOpen, setIsGitHubDialogOpen] = useState(false);
  const [isWebsiteDialogOpen, setIsWebsiteDialogOpen] = useState(false);
  const [githubUsername, setGitHubUsername] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionResult, setConnectionResult] = useState<string | null>(null);



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

  const generateNewsletterNow = async () => {
    if (!user) return;
    
    setIsGeneratingNewsletter(true);
    setNewsletterGenerationResult(null);
    setGeneratedNewsletter(null);
    
    try {
      // Generate newsletter with default configuration
      const result = await api.generateNewsletter({
        user_id: user.user_id,
        newsletter_config: {
          instructions: "Create a friendly, engaging newsletter highlighting recent life events and updates.",
          periodicity: 168, // Past week (168 hours)
          visibility: [
            { type: "good_friends", name: "Good Friends" }
          ],
          name: "Weekly Update"
        }
      });
      
      if (result.success && result.content) {
        setGeneratedNewsletter(result.content);
        setNewsletterGenerationResult(`Newsletter generated successfully! Found ${result.events_count} recent events.`);
      } else {
        throw new Error(result.error_message || 'Failed to generate newsletter');
      }
    } catch (error) {
      console.error('Newsletter generation error:', error);
      setNewsletterGenerationResult('Failed to generate newsletter. Please try again.');
    } finally {
      setIsGeneratingNewsletter(false);
      // Clear the message after 10 seconds
      setTimeout(() => setNewsletterGenerationResult(null), 10000);
    }
  };

  const sendGeneratedNewsletter = async () => {
    if (!generatedNewsletter) return;
    
    setIsSendingNewsletter(true);
    setNewsletterSendResult(null);
    
    try {
      // Use the actual backend endpoint to send to all subscribers
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

  const handleConnectGitHub = async () => {
    if (!githubUsername.trim()) return;
    
    setIsConnecting(true);
    setConnectionResult(null);
    
    try {
      // Create a temporary session for the connection
      const session = await api.startOnboarding();
      
      const result = await api.connectGitHub(session.session_id, githubUsername);
      
      if (result.success) {
        setConnectionResult(`✅ Successfully connected GitHub profile: ${githubUsername}`);
        setGitHubUsername('');
        setIsGitHubDialogOpen(false);
      } else {
        throw new Error(result.message || 'Failed to connect GitHub');
      }
    } catch (error) {
      console.error('GitHub connection error:', error);
      setConnectionResult(`❌ Failed to connect GitHub: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsConnecting(false);
      // Clear the message after 5 seconds
      setTimeout(() => setConnectionResult(null), 5000);
    }
  };

  const handleConnectWebsite = async () => {
    if (!websiteUrl.trim()) return;
    
    setIsConnecting(true);
    setConnectionResult(null);
    
    try {
      // Create a temporary session for the connection
      const session = await api.startOnboarding();
      
      const result = await api.connectWebsite(session.session_id, websiteUrl);
      
      if (result.success) {
        setConnectionResult(`✅ Successfully connected website: ${websiteUrl}`);
        setWebsiteUrl('');
        setIsWebsiteDialogOpen(false);
      } else {
        throw new Error(result.message || 'Failed to connect website');
      }
    } catch (error) {
      console.error('Website connection error:', error);
      setConnectionResult(`❌ Failed to connect website: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsConnecting(false);
      // Clear the message after 5 seconds
      setTimeout(() => setConnectionResult(null), 5000);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
        <AuthenticatedHeader />
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
        <AuthenticatedHeader />
        <div className="container mx-auto px-6 py-8 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error || 'Failed to load user data'}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={() => window.location.reload()}>Retry</Button>
              <Button variant="outline" onClick={() => window.location.href = '/login'}>
                Login
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <AuthenticatedHeader />
      
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
                <div className="flex gap-2">
                  <Button 
                    size="lg"
                    className="px-6 py-3"
                    onClick={generateNewsletterNow}
                    disabled={isGeneratingNewsletter}
                  >
                    {isGeneratingNewsletter ? '⏳ Generating...' : '📝 Generate Newsletter Now'}
                  </Button>
                  {generatedNewsletter && (
                    <Button 
                      size="lg"
                      variant="outline"
                      className="px-6 py-3"
                      onClick={sendGeneratedNewsletter}
                      disabled={isSendingNewsletter}
                    >
                      {isSendingNewsletter ? '⏳ Sending...' : '📧 Send Newsletter'}
                    </Button>
                  )}
                </div>
                {newsletterGenerationResult && (
                  <p className={`text-sm px-3 py-1 rounded ${
                    newsletterGenerationResult.includes('successfully') 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {newsletterGenerationResult}
                  </p>
                )}
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
          <div className="grid md:grid-cols-5 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Friends</p>
                    <p className="text-2xl font-bold text-foreground">{friends.length}</p>
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
                    <p className="text-sm text-muted-foreground">Timeline Entries</p>
                    <p className="text-2xl font-bold text-foreground">{timeline.length}</p>
                  </div>
                  <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center">
                    <span className="text-secondary">📝</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Subscribers</p>
                    <p className="text-2xl font-bold text-foreground">{subscriberCount}</p>
                  </div>
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                    <span className="text-accent">📧</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Life Events</p>
                    <p className="text-2xl font-bold text-foreground">{lifeEvents.length}</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600">🎯</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">User Facts</p>
                    <p className="text-2xl font-bold text-foreground">{lifeFacts.length}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600">💡</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Tabs */}
          <Tabs defaultValue="newsletter" className="space-y-6">
            <TabsList className="grid w-full grid-cols-7">
              <TabsTrigger value="newsletter">Newsletter</TabsTrigger>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="friends">Friends</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="life-events">Life Events</TabsTrigger>
              <TabsTrigger value="user-facts">User Facts</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

            {/* Newsletter Tab */}
            <TabsContent value="newsletter" className="space-y-6">
              {generatedNewsletter && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      📝 Generated Newsletter
                      <Badge variant="outline" className="bg-green-50 text-green-700">Ready to Send</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 p-6 rounded-lg border">
                      <div 
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{
                          __html: generatedNewsletter.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/# (.*?)(<br\/>)/g, '<h1 class="text-xl font-bold mb-4">$1</h1>').replace(/## (.*?)(<br\/>)/g, '<h2 class="text-lg font-semibold mb-3">$2</h2>')
                        }}
                      />
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button 
                        variant="outline"
                        onClick={generateNewsletterNow}
                        disabled={isGeneratingNewsletter}
                      >
                        {isGeneratingNewsletter ? '⏳ Regenerating...' : '🔄 Regenerate'}
                      </Button>
                      <Button 
                        onClick={sendGeneratedNewsletter}
                        disabled={isSendingNewsletter}
                      >
                        {isSendingNewsletter ? '⏳ Sending...' : '📧 Send Newsletter'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
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

            {/* Life Events Tab */}
            <TabsContent value="life-events" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    Life Events Timeline
                    <Badge variant="outline">{lifeEvents.length} events</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {lifeEvents.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <p className="text-lg mb-2">🎯 No life events yet</p>
                        <p>Add content to create your life events timeline</p>
                      </div>
                    ) : (
                      lifeEvents.map((event, index) => (
                        <div key={event.event_id} className="border-l-4 border-primary pl-6 pb-6 relative">
                          {index !== lifeEvents.length - 1 && (
                            <div className="absolute left-0 top-8 w-px h-full bg-border"></div>
                          )}
                          <div className="absolute left-[-4px] top-2 w-2 h-2 bg-primary rounded-full"></div>
                          
                          <div className="flex items-start justify-between mb-2">
                            <h3 className="font-medium text-foreground">{event.summary}</h3>
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary" className="text-xs">
                                {event.visibility || 'public'}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(event.start_date).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          
                          {event.end_date && (
                            <p className="text-sm text-muted-foreground mb-2">
                              Duration: {new Date(event.start_date).toLocaleDateString()} - {new Date(event.end_date).toLocaleDateString()}
                            </p>
                          )}
                          
                          {event.associated_docs && event.associated_docs.length > 0 && (
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-xs text-muted-foreground">Documents:</span>
                              <Badge variant="outline" className="text-xs">
                                {event.associated_docs.length} attached
                              </Badge>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                  
                  {lifeEvents.length > 0 && (
                    <div className="mt-6 pt-6 border-t">
                      <p className="text-sm text-muted-foreground text-center">
                        💡 These events are automatically processed from your content and used to generate personalized newsletters
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* User Facts Tab */}
            <TabsContent value="user-facts" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    User Facts
                    <Badge variant="outline">{lifeFacts.length} facts</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {lifeFacts.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <p className="text-lg mb-2">💡 No user facts yet</p>
                        <p>Add content to create your user facts collection</p>
                      </div>
                    ) : (
                      <div className="grid gap-4">
                        {lifeFacts.map((fact: any) => (
                          <div key={fact.fact_id} className="p-4 border border-border rounded-lg">
                            <div className="flex items-start justify-between mb-3">
                              <h3 className="font-medium text-foreground">{fact.summary}</h3>
                              <div className="flex items-center gap-2">
                                {fact.category && (
                                  <Badge variant="secondary" className="text-xs">
                                    {fact.category}
                                  </Badge>
                                )}
                                <Badge variant="outline" className="text-xs">
                                  {fact.visibility || 'public'}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(fact.created_at).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                            
                            {fact.description && (
                              <p className="text-sm text-muted-foreground mb-3">
                                {fact.description}
                              </p>
                            )}
                            
                            {fact.associated_docs && fact.associated_docs.length > 0 && (
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-xs text-muted-foreground">Documents:</span>
                                <Badge variant="outline" className="text-xs">
                                  {fact.associated_docs.length} attached
                                </Badge>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {lifeFacts.length > 0 && (
                    <div className="mt-6 pt-6 border-t">
                      <p className="text-sm text-muted-foreground text-center">
                        💡 These facts are automatically processed from your content and represent key information about you
                      </p>
                    </div>
                  )}
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
                  <CardTitle>Data Sources</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg">📃</span>
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">Personal Website</h4>
                        <p className="text-sm text-muted-foreground">Add content from any website or blog</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => setIsWebsiteDialogOpen(true)}>Add Website</Button>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg">💻</span>
                      </div>
                      <div>
                        <h4 className="font-medium text-foreground">GitHub</h4>
                        <p className="text-sm text-muted-foreground">Connect your repositories and projects</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => setIsGitHubDialogOpen(true)}>Connect GitHub</Button>
                  </div>
                  
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      Connect external data sources to enrich your AI&apos;s knowledge about your life and activities. This helps create better newsletter content.
                    </p>
                  </div>
                  
                  {connectionResult && (
                    <div className={`p-3 rounded-md text-sm ${
                      connectionResult.includes('✅') 
                        ? 'bg-green-50 text-green-800 border border-green-200' 
                        : 'bg-red-50 text-red-800 border border-red-200'
                    }`}>
                      {connectionResult}
                    </div>
                  )}
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

      {/* GitHub Connection Dialog */}
      <Dialog open={isGitHubDialogOpen} onOpenChange={setIsGitHubDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect GitHub</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Enter your GitHub username to connect your repositories and projects to your AI profile.
            </p>
            <Input
              label="GitHub Username"
              placeholder="e.g. octocat"
              value={githubUsername}
              onChange={(e) => setGitHubUsername(e.target.value)}
            />
            <div className="flex gap-2">
              <Button 
                onClick={handleConnectGitHub} 
                disabled={!githubUsername.trim() || isConnecting}
                className="flex-1"
              >
                {isConnecting ? 'Connecting...' : 'Connect GitHub'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setIsGitHubDialogOpen(false)}
                disabled={isConnecting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Website Connection Dialog */}
      <Dialog open={isWebsiteDialogOpen} onOpenChange={setIsWebsiteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Website</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Enter a website URL to scrape content and add it to your AI knowledge base.
            </p>
            <Input
              label="Website URL"
              placeholder="https://example.com"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              type="url"
            />
            <div className="flex gap-2">
              <Button 
                onClick={handleConnectWebsite} 
                disabled={!websiteUrl.trim() || isConnecting}
                className="flex-1"
              >
                {isConnecting ? 'Connecting...' : 'Add Website'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setIsWebsiteDialogOpen(false)}
                disabled={isConnecting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DashboardPageFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <AuthenticatedHeader />
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
    <ProtectedRoute>
      <Suspense fallback={<DashboardPageFallback />}>
        <DashboardContent />
      </Suspense>
    </ProtectedRoute>
  );
}
