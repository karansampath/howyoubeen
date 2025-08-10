"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mail, User, Clock, Shield } from 'lucide-react';

interface NewsletterSubscriptionProps {
  linkCode: string;
  username?: string;
  privacyLevel?: string;
  onSubscribe?: (data: SubscriptionData) => void;
  isLoading?: boolean;
}

interface SubscriptionData {
  email: string;
  frequency: string;
  name?: string;
}

const frequencyOptions = [
  { value: 'daily', label: 'Daily', description: 'Get updates every day' },
  { value: 'weekly', label: 'Weekly', description: 'Get updates once a week' },
  { value: 'monthly', label: 'Monthly', description: 'Get updates once a month' }
];

const privacyLevelDescriptions = {
  close_family: { label: 'Close Family', icon: '👨‍👩‍👧‍👦', description: 'Most personal updates and family moments' },
  best_friends: { label: 'Best Friends', icon: '👥', description: 'Personal updates and close friend activities' },
  good_friends: { label: 'Good Friends', icon: '🤝', description: 'Social updates and general life events' },
  acquaintances: { label: 'Acquaintances', icon: '👋', description: 'Professional updates and public achievements' },
  public: { label: 'Public', icon: '🌐', description: 'Public posts and general announcements' }
};

export default function NewsletterSubscription({ 
  linkCode, 
  username, 
  privacyLevel, 
  onSubscribe,
  isLoading = false 
}: NewsletterSubscriptionProps) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [frequency, setFrequency] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !frequency) return;

    setIsSubmitting(true);
    
    try {
      const subscriptionData = { email, frequency, name: name || undefined };
      
      if (onSubscribe) {
        await onSubscribe(subscriptionData);
      } else {
        // Default API call
        const response = await fetch('/api/newsletter/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            privacy_code: linkCode,
            subscriber_email: email,
            frequency: frequency,
            subscriber_name: name || null
          })
        });

        if (response.ok) {
          setSuccess(true);
        } else {
          throw new Error('Subscription failed');
        }
      }
    } catch (error) {
      console.error('Subscription error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const privacyInfo = privacyLevel && privacyLevelDescriptions[privacyLevel as keyof typeof privacyLevelDescriptions];

  if (success) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Successfully Subscribed!</h3>
            <p className="text-gray-600 mb-4">
              You&apos;ll receive {frequency} updates from {username || 'this user'} at {email}
            </p>
            <p className="text-sm text-gray-500">
              Check your email for a confirmation and unsubscribe instructions.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="w-5 h-5" />
          Subscribe to Newsletter
        </CardTitle>
        {username && (
          <CardDescription>
            Stay updated with {username}&apos;s latest activities
          </CardDescription>
        )}
      </CardHeader>
      
      <CardContent className="space-y-4">
        {privacyInfo && (
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium">Privacy Level</span>
            </div>
            <Badge variant="secondary" className="mb-2">
              {privacyInfo.icon} {privacyInfo.label}
            </Badge>
            <p className="text-xs text-gray-600">{privacyInfo.description}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email Address *
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              required
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-1">
              Your Name (Optional)
            </label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="How should we address you?"
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label htmlFor="frequency" className="block text-sm font-medium mb-1">
              Frequency *
            </label>
            <Select value={frequency} onValueChange={setFrequency} disabled={isSubmitting || isLoading}>
              <SelectTrigger>
                <SelectValue placeholder="How often do you want updates?" />
              </SelectTrigger>
              <SelectContent>
                {frequencyOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <div>
                        <div className="font-medium">{option.label}</div>
                        <div className="text-xs text-gray-500">{option.description}</div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={!email || !frequency || isSubmitting || isLoading}
          >
            {isSubmitting ? 'Subscribing...' : 'Subscribe to Newsletter'}
          </Button>
        </form>

        <div className="text-xs text-gray-500 text-center">
          You can unsubscribe at any time. We respect your privacy and will never share your email.
        </div>
      </CardContent>
    </Card>
  );
}
