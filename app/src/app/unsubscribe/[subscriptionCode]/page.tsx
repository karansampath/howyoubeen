'use client';

import { Suspense, useEffect, useState } from 'react';
import { notFound } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mail, UserX, CheckCircle, AlertCircle } from 'lucide-react';

interface UnsubscribePageProps {
  params: Promise<{
    subscriptionCode: string;
  }>;
}

interface SubscriptionDetails {
  id: string;
  sourceUsername: string;
  sourceFullName: string;
  subscriberEmail: string;
  privacyLevel: string;
  frequency: string;
  status: string;
}

// Mock function - replace with actual API call
async function getSubscriptionDetails(subscriptionCode: string): Promise<SubscriptionDetails | null> {
  // In a real app, this would call your API
  const mockSubscriptions = {
    'sub-sarah-1234': {
      id: 'sub-sarah-1234',
      sourceUsername: 'sarah_codes',
      sourceFullName: 'Sarah Johnson',
      subscriberEmail: 'friend@example.com',
      privacyLevel: 'best_friends',
      frequency: 'weekly',
      status: 'active'
    },
    'sub-mike-5678': {
      id: 'sub-mike-5678', 
      sourceUsername: 'world_wanderer_mike',
      sourceFullName: 'Mike Chen',
      subscriberEmail: 'traveler@example.com',
      privacyLevel: 'public',
      frequency: 'daily',
      status: 'active'
    },
    'sub-emma-9012': {
      id: 'sub-emma-9012',
      sourceUsername: 'family_life_emma', 
      sourceFullName: 'Emma Rodriguez',
      subscriberEmail: 'family@example.com',
      privacyLevel: 'close_family',
      frequency: 'weekly',
      status: 'active'
    }
  };

  return mockSubscriptions[subscriptionCode as keyof typeof mockSubscriptions] || null;
}

async function unsubscribeFromNewsletter(subscriptionCode: string): Promise<{ success: boolean; message: string }> {
  // In a real app, this would call your API
  console.log('Unsubscribing:', subscriptionCode);
  
  // Mock successful unsubscription
  return {
    success: true,
    message: 'Successfully unsubscribed from newsletter'
  };
}

const privacyLevels = {
  close_family: { label: 'Close Family', icon: '👨‍👩‍👧‍👦', color: 'bg-purple-100 text-purple-800' },
  best_friends: { label: 'Best Friends', icon: '👥', color: 'bg-blue-100 text-blue-800' },
  good_friends: { label: 'Good Friends', icon: '🤝', color: 'bg-green-100 text-green-800' },
  acquaintances: { label: 'Acquaintances', icon: '👋', color: 'bg-yellow-100 text-yellow-800' },
  public: { label: 'Public', icon: '🌐', color: 'bg-gray-100 text-gray-800' }
};

const frequencies = {
  daily: { label: 'Daily', icon: '📅' },
  weekly: { label: 'Weekly', icon: '📆' },
  monthly: { label: 'Monthly', icon: '🗓️' }
};

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-pulse">
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="h-6 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

async function UnsubscribePageContent({ subscriptionCode }: { subscriptionCode: string }) {
  const subscription = await getSubscriptionDetails(subscriptionCode);

  if (!subscription) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Invalid Unsubscribe Link</h2>
            <p className="text-gray-600 mb-4">
              This unsubscribe link is not valid or has already been used.
            </p>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              Go to Homepage
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (subscription.status === 'unsubscribed') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Already Unsubscribed</h2>
            <p className="text-gray-600 mb-4">
              You have already unsubscribed from {subscription.sourceFullName}&apos;s newsletter.
            </p>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              Go to Homepage
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleUnsubscribe = async () => {
    const result = await unsubscribeFromNewsletter(subscriptionCode);
    if (result.success) {
      // In a real app, you would update the UI state or redirect
      window.location.reload();
    }
  };

  const privacyInfo = privacyLevels[subscription.privacyLevel as keyof typeof privacyLevels];
  const frequencyInfo = frequencies[subscription.frequency as keyof typeof frequencies];

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserX className="w-5 h-5" />
              Unsubscribe from Newsletter
            </CardTitle>
            <CardDescription>
              Confirm that you want to unsubscribe from this newsletter
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Subscription Details */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <Mail className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium">{subscription.sourceFullName}</p>
                  <p className="text-sm text-gray-600">@{subscription.sourceUsername}</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Email:</span>
                  <span className="text-sm font-medium">{subscription.subscriberEmail}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Privacy Level:</span>
                  <Badge variant="secondary" className={privacyInfo.color}>
                    {privacyInfo.icon} {privacyInfo.label}
                  </Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Frequency:</span>
                  <Badge variant="outline">
                    {frequencyInfo.icon} {frequencyInfo.label}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Warning */}
            <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ Once you unsubscribe, you&apos;ll stop receiving all newsletter updates from {subscription.sourceFullName}. 
                You can always resubscribe later using their newsletter link.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button 
                variant="destructive" 
                className="flex-1"
                onClick={handleUnsubscribe}
              >
                <UserX className="w-4 h-4 mr-2" />
                Unsubscribe
              </Button>
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => window.history.back()}
              >
                Cancel
              </Button>
            </div>

            {/* Alternative Action */}
            <div className="text-center pt-4 border-t">
              <p className="text-sm text-gray-600 mb-2">
                Want to stay connected differently?
              </p>
              <Button 
                variant="link" 
                onClick={() => window.location.href = `https://howyoubeen.com/${subscription.sourceUsername}`}
              >
                Chat with {subscription.sourceFullName} instead
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>
            Powered by <strong>HowYouBeen</strong> - AI-powered social connections
          </p>
        </div>
      </div>
    </div>
  );
}

export default function UnsubscribePage({ params }: UnsubscribePageProps) {
  const [subscriptionCode, setSubscriptionCode] = useState<string | null>(null);
  
  useEffect(() => {
    const getParams = async () => {
      const resolvedParams = await params;
      setSubscriptionCode(resolvedParams.subscriptionCode);
    };
    
    getParams();
  }, [params]);
  
  if (!subscriptionCode) {
    return <LoadingSkeleton />;
  }
  
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <UnsubscribePageContent subscriptionCode={subscriptionCode} />
    </Suspense>
  );
}

// Note: generateStaticParams removed because client components cannot export it
