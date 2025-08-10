"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Mail, 
  Users, 
  Link, 
  Copy, 
  Calendar,
  Shield,
  TrendingUp,
  Settings
} from 'lucide-react';

interface NewsletterSubscription {
  subscription_id: string;
  subscriber_email: string;
  privacy_level: string;
  frequency: string;
  status: string;
  last_sent?: string;
  created_at: string;
}

interface PrivacyLink {
  privacy_level: string;
  link: string;
  subscribers_count: number;
}

interface NewsletterManagerProps {
  userId: string;
  username: string;
}

const privacyLevels = {
  close_family: { label: 'Close Family', icon: '👨‍👩‍👧‍👦', color: 'bg-purple-100 text-purple-800' },
  best_friends: { label: 'Best Friends', icon: '👥', color: 'bg-blue-100 text-blue-800' },
  good_friends: { label: 'Good Friends', icon: '🤝', color: 'bg-green-100 text-green-800' },
  acquaintances: { label: 'Acquaintances', icon: '👋', color: 'bg-yellow-100 text-yellow-800' },
  public: { label: 'Public', icon: '🌐', color: 'bg-gray-100 text-gray-800' }
};

const frequencies = {
  daily: { label: 'Daily', icon: '📅', color: 'bg-red-100 text-red-800' },
  weekly: { label: 'Weekly', icon: '📆', color: 'bg-orange-100 text-orange-800' },
  monthly: { label: 'Monthly', icon: '🗓️', color: 'bg-indigo-100 text-indigo-800' }
};

export default function NewsletterManager({ userId, username }: NewsletterManagerProps) {
  const [subscriptions, setSubscriptions] = useState<NewsletterSubscription[]>([]);
  const [privacyLinks, setPrivacyLinks] = useState<PrivacyLink[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedLink, setCopiedLink] = useState('');

  useEffect(() => {
    loadSubscriptions();
    loadPrivacyLinks();
  }, [userId]);

  const loadSubscriptions = async () => {
    try {
      const response = await fetch(`/api/newsletter/subscriptions/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
      }
    } catch (error) {
      console.error('Failed to load subscriptions:', error);
    }
  };

  const loadPrivacyLinks = async () => {
    // In a real implementation, you'd fetch these from your API
    const mockLinks: PrivacyLink[] = [
      { privacy_level: 'best_friends', link: `https://howyoubeen.com/subscribe/bf-${username}-abc123`, subscribers_count: 5 },
      { privacy_level: 'good_friends', link: `https://howyoubeen.com/subscribe/gf-${username}-def456`, subscribers_count: 12 },
      { privacy_level: 'public', link: `https://howyoubeen.com/subscribe/public-${username}-ghi789`, subscribers_count: 28 }
    ];
    setPrivacyLinks(mockLinks);
    setIsLoading(false);
  };

  const handleCopyLink = async (link: string, privacyLevel: string) => {
    try {
      await navigator.clipboard.writeText(link);
      setCopiedLink(privacyLevel);
      setTimeout(() => setCopiedLink(''), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
    }
  };

  const getSubscriptionStats = () => {
    const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');
    const byFrequency = activeSubscriptions.reduce((acc, sub) => {
      acc[sub.frequency] = (acc[sub.frequency] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: activeSubscriptions.length,
      byFrequency
    };
  };

  const stats = getSubscriptionStats();

  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Mail className="w-6 h-6" />
            Newsletter Manager
          </h1>
          <p className="text-gray-600">Manage your newsletter subscriptions and sharing links</p>
        </div>
        <Badge variant="secondary" className="text-lg px-3 py-1">
          {stats.total} Active Subscribers
        </Badge>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-600">Total Subscribers</span>
            </div>
            <p className="text-2xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
        
        {Object.entries(frequencies).map(([freq, config]) => (
          <Card key={freq}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <span className="text-lg">{config.icon}</span>
                <span className="text-sm text-gray-600">{config.label}</span>
              </div>
              <p className="text-2xl font-bold">{stats.byFrequency[freq] || 0}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="subscribers" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="subscribers">Subscribers</TabsTrigger>
          <TabsTrigger value="links">Sharing Links</TabsTrigger>
        </TabsList>

        <TabsContent value="subscribers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Newsletter Subscribers</CardTitle>
              <CardDescription>
                People who receive your newsletter updates
              </CardDescription>
            </CardHeader>
            <CardContent>
              {subscriptions.length === 0 ? (
                <div className="text-center py-8">
                  <Mail className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No subscribers yet</p>
                  <p className="text-sm text-gray-400">Share your newsletter links to get started!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {subscriptions.map((subscription) => (
                    <div key={subscription.subscription_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                          <Mail className="w-5 h-5 text-gray-600" />
                        </div>
                        <div>
                          <p className="font-medium">{subscription.subscriber_email}</p>
                          <div className="flex gap-2 mt-1">
                            <Badge 
                              variant="secondary" 
                              className={privacyLevels[subscription.privacy_level as keyof typeof privacyLevels]?.color}
                            >
                              {privacyLevels[subscription.privacy_level as keyof typeof privacyLevels]?.icon}
                              {privacyLevels[subscription.privacy_level as keyof typeof privacyLevels]?.label}
                            </Badge>
                            <Badge 
                              variant="outline"
                              className={frequencies[subscription.frequency as keyof typeof frequencies]?.color}
                            >
                              {frequencies[subscription.frequency as keyof typeof frequencies]?.icon}
                              {frequencies[subscription.frequency as keyof typeof frequencies]?.label}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
                          {subscription.status}
                        </Badge>
                        {subscription.last_sent && (
                          <p className="text-xs text-gray-500 mt-1">
                            Last sent: {new Date(subscription.last_sent).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="links" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Newsletter Sharing Links</CardTitle>
              <CardDescription>
                Share these links to let friends subscribe to your newsletter at different privacy levels
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {privacyLinks.map((linkData) => (
                <div key={linkData.privacy_level} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      <Badge className={privacyLevels[linkData.privacy_level as keyof typeof privacyLevels]?.color}>
                        {privacyLevels[linkData.privacy_level as keyof typeof privacyLevels]?.icon}
                        {privacyLevels[linkData.privacy_level as keyof typeof privacyLevels]?.label}
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {linkData.subscribers_count} subscribers
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={linkData.link}
                      readOnly
                      className="flex-1 px-3 py-2 border rounded text-sm bg-gray-50"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopyLink(linkData.link, linkData.privacy_level)}
                    >
                      {copiedLink === linkData.privacy_level ? (
                        <>✓ Copied</>
                      ) : (
                        <><Copy className="w-4 h-4 mr-1" /> Copy</>
                      )}
                    </Button>
                  </div>
                </div>
              ))}
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 <strong>Tip:</strong> Share different privacy level links with different groups of friends. 
                  Family gets the close family link, work colleagues get the acquaintances link, etc.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
