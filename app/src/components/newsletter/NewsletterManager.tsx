"use client";

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Mail, 
  Users, 
  Link, 
  Copy, 
  Shield,
  TrendingUp,
  Share2,
  UserPlus
} from 'lucide-react';
import { api } from '@/lib/api';

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

interface ReferralLink {
  referral_id: string;
  friend_name: string;
  friend_email?: string;
  privacy_level: string;
  referral_link: string;
  referral_code: string;
  clicks: number;
  conversions: number;
  is_active: boolean;
  created_at: string;
}

interface Referral {
  subscription_id: string;
  subscriber_email: string;
  subscriber_name?: string;
  privacy_level: string;
  frequency: string;
  referrer_name?: string;
  created_at: string;
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
  const [referralLinks, setReferralLinks] = useState<ReferralLink[]>([]);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedLink, setCopiedLink] = useState('');
  
  // Referral link creation state
  const [newReferral, setNewReferral] = useState({
    friend_name: '',
    friend_email: '',
    privacy_level: 'good_friends'
  });
  const [isCreatingReferral, setIsCreatingReferral] = useState(false);

  const loadSubscriptions = useCallback(async () => {
    try {
      const data = await api.getUserSubscriptions(userId);
      setSubscriptions(data.subscriptions || []);
    } catch (error) {
      console.error('Failed to load subscriptions:', error);
    }
  }, [userId]);

  const loadPrivacyLinks = useCallback(async () => {
    try {
      const privacyLevelKeys = Object.keys(privacyLevels);
      const linkPromises = privacyLevelKeys.map(async (level) => {
        try {
          const response = await api.createSubscriptionLink(userId, level);
          const subscribersForLevel = subscriptions.filter(sub => sub.privacy_level === level).length;
          return {
            privacy_level: level,
            link: response.link,
            subscribers_count: subscribersForLevel
          };
        } catch (error) {
          console.error(`Failed to create link for ${level}:`, error);
          return {
            privacy_level: level,
            link: `https://howyoubeen.com/subscribe/${level}-${username}-error`,
            subscribers_count: 0
          };
        }
      });

      const links = await Promise.all(linkPromises);
      setPrivacyLinks(links);
    } catch (error) {
      console.error('Failed to load privacy links:', error);
    } finally {
      setIsLoading(false);
    }
  }, [userId, username, subscriptions]);

  const loadReferralLinks = useCallback(async () => {
    try {
      const data = await api.getUserReferralLinks(userId);
      setReferralLinks(data.referral_links || []);
    } catch (error) {
      console.error('Failed to load referral links:', error);
    }
  }, [userId]);

  const loadReferrals = useCallback(async () => {
    try {
      const data = await api.getUserReferrals(userId);
      setReferrals(data.referrals || []);
    } catch (error) {
      console.error('Failed to load referrals:', error);
    }
  }, [userId]);

  useEffect(() => {
    loadSubscriptions();
    loadPrivacyLinks();
    loadReferralLinks();
    loadReferrals();
  }, [loadSubscriptions, loadPrivacyLinks, loadReferralLinks, loadReferrals]);

  const handleCopyLink = async (link: string, privacyLevel: string) => {
    try {
      await navigator.clipboard.writeText(link);
      setCopiedLink(privacyLevel);
      setTimeout(() => setCopiedLink(''), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
    }
  };

  const createReferralLink = async () => {
    if (!newReferral.friend_name.trim()) return;
    
    setIsCreatingReferral(true);
    try {
      const result = await api.createReferralLink({
        user_id: userId,
        created_by_user_id: userId,
        friend_name: newReferral.friend_name,
        friend_email: newReferral.friend_email || undefined,
        privacy_level: newReferral.privacy_level
      });
      
      if (result.success) {
        await loadReferralLinks(); // Reload referral links
        setNewReferral({
          friend_name: '',
          friend_email: '',
          privacy_level: 'good_friends'
        });

      } else {
        console.error('Failed to create referral link:', result.message);
      }
    } catch (error) {
      console.error('Failed to create referral link:', error);
    } finally {
      setIsCreatingReferral(false);
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="subscribers">Subscribers</TabsTrigger>
          <TabsTrigger value="links">Sharing Links</TabsTrigger>
          <TabsTrigger value="referrals">Referrals</TabsTrigger>
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

        <TabsContent value="referrals" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Create Referral Links */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="w-5 h-5" />
                  Create Referral Link
                </CardTitle>
                <CardDescription>
                  Generate a personalized link to invite friends to your newsletter
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Friend&apos;s Name</label>
                  <Input
                    placeholder="Enter friend's name"
                    value={newReferral.friend_name}
                    onChange={(e) => setNewReferral({...newReferral, friend_name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Friend&apos;s Email (Optional)</label>
                  <Input
                    type="email"
                    placeholder="friend@example.com"
                    value={newReferral.friend_email}
                    onChange={(e) => setNewReferral({...newReferral, friend_email: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Privacy Level</label>
                  <Select value={newReferral.privacy_level} onValueChange={(value) => setNewReferral({...newReferral, privacy_level: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select privacy level" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(privacyLevels).map(([key, level]) => (
                        <SelectItem key={key} value={key}>
                          {level.icon} {level.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  onClick={createReferralLink} 
                  disabled={!newReferral.friend_name.trim() || isCreatingReferral}
                  className="w-full"
                >
                  {isCreatingReferral ? 'Creating...' : 'Create Referral Link'}
                </Button>
              </CardContent>
            </Card>

            {/* Referral Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Referral Performance
                </CardTitle>
                <CardDescription>
                  Track your referral link performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{referralLinks.reduce((sum, link) => sum + link.clicks, 0)}</div>
                    <div className="text-sm text-gray-600">Total Clicks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{referrals.length}</div>
                    <div className="text-sm text-gray-600">Referral Subscriptions</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{referralLinks.length}</div>
                    <div className="text-sm text-gray-600">Active Links</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {referralLinks.length > 0 ? Math.round((referrals.length / referralLinks.reduce((sum, link) => sum + link.clicks, 0)) * 100) || 0 : 0}%
                    </div>
                    <div className="text-sm text-gray-600">Conversion Rate</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Referral Links */}
          <Card>
            <CardHeader>
              <CardTitle>Your Referral Links</CardTitle>
              <CardDescription>
                Manage and track your personalized referral links
              </CardDescription>
            </CardHeader>
            <CardContent>
              {referralLinks.length === 0 ? (
                <div className="text-center py-8">
                  <Share2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No referral links created yet</p>
                  <p className="text-sm text-gray-400">Create personalized links to invite friends!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {referralLinks.map((link) => (
                    <div key={link.referral_id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="font-medium">{link.friend_name}</h3>
                          {link.friend_email && (
                            <p className="text-sm text-gray-600">{link.friend_email}</p>
                          )}
                        </div>
                        <Badge className={privacyLevels[link.privacy_level as keyof typeof privacyLevels]?.color}>
                          {privacyLevels[link.privacy_level as keyof typeof privacyLevels]?.icon}
                          {privacyLevels[link.privacy_level as keyof typeof privacyLevels]?.label}
                        </Badge>
                      </div>
                      
                      <div className="flex gap-2 mb-3">
                        <input
                          type="text"
                          value={link.referral_link}
                          readOnly
                          className="flex-1 px-3 py-2 border rounded text-sm bg-gray-50"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCopyLink(link.referral_link, link.referral_id)}
                        >
                          {copiedLink === link.referral_id ? (
                            <>✓ Copied</>
                          ) : (
                            <><Copy className="w-4 h-4 mr-1" /> Copy</>
                          )}
                        </Button>
                      </div>
                      
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>{link.clicks} clicks</span>
                        <span>{link.conversions} conversions</span>
                        <span>Created {new Date(link.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Referred Subscribers */}
          <Card>
            <CardHeader>
              <CardTitle>Referred Subscribers</CardTitle>
              <CardDescription>
                People who subscribed through your referral links
              </CardDescription>
            </CardHeader>
            <CardContent>
              {referrals.length === 0 ? (
                <div className="text-center py-8">
                  <UserPlus className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No referral subscriptions yet</p>
                  <p className="text-sm text-gray-400">Share your referral links to get started!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {referrals.map((referral) => (
                    <div key={referral.subscription_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <UserPlus className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                          <p className="font-medium">
                            {referral.subscriber_name || referral.subscriber_email}
                          </p>
                          {referral.subscriber_name && (
                            <p className="text-sm text-gray-600">{referral.subscriber_email}</p>
                          )}
                          {referral.referrer_name && (
                            <p className="text-xs text-gray-500">Referred by {referral.referrer_name}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex gap-2 mb-1">
                          <Badge 
                            variant="secondary" 
                            className={privacyLevels[referral.privacy_level as keyof typeof privacyLevels]?.color}
                          >
                            {privacyLevels[referral.privacy_level as keyof typeof privacyLevels]?.icon}
                            {privacyLevels[referral.privacy_level as keyof typeof privacyLevels]?.label}
                          </Badge>
                          <Badge 
                            variant="outline"
                            className={frequencies[referral.frequency as keyof typeof frequencies]?.color}
                          >
                            {frequencies[referral.frequency as keyof typeof frequencies]?.icon}
                            {frequencies[referral.frequency as keyof typeof frequencies]?.label}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-500">
                          {new Date(referral.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
