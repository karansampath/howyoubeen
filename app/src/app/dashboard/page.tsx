'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Header } from '@/components/layout/Header';
import { api, type User } from '@/lib/api';

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats] = useState({
    totalFriends: 2,
    monthlyInteractions: 15,
    profileViews: 28,
    newsletterSubscribers: 1
  });

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

  const handleLogout = () => {
    // In real app, clear auth state and redirect
    window.location.href = '/';
  };

  const addFriend = () => {
    // In real app, call API to add friend
    console.log('Adding friend:', newFriend);
    setIsAddFriendOpen(false);
    setNewFriend({ name: '', email: '', level: 'good_friends', context: '' });
  };

  const uploadContent = () => {
    if (!newContent.trim()) return;
    // In real app, call API to upload content
    console.log('Uploading content:', newContent);
    setNewContent('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <Header user={user} onLogout={handleLogout} />
      
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-6xl mx-auto">
          
          {/* Header Section */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Welcome back, {user.full_name}
            </h1>
            <p className="text-muted-foreground">
              Manage your AI profile and see how friends are connecting with you
            </p>
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
                    <p className="text-sm text-muted-foreground">Monthly Chats</p>
                    <p className="text-2xl font-bold text-foreground">{stats.monthlyInteractions}</p>
                  </div>
                  <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center">
                    <span className="text-secondary">💬</span>
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
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="friends">Friends</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

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
                        placeholder="friend@example.com"
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
                    <Input label="Full Name" value={user.full_name} readOnly />
                    <Input label="Username" value={user.username} readOnly />
                  </div>
                  <Input label="Email" value={user.email} readOnly />
                  <Textarea label="Bio" value={user.bio} rows={3} />
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
