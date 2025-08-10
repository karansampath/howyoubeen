import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import NewsletterSubscription from '@/components/newsletter/NewsletterSubscription';
import { Card, CardContent } from '@/components/ui/card';
import { Mail, User } from 'lucide-react';
import { api } from '@/lib/api';

interface SubscribePageProps {
  params: Promise<{
    linkCode: string;
  }>;
}

// Get subscription info from API
async function getSubscriptionInfo(linkCode: string) {
  try {
    const subscriptionInfo = await api.getSubscriptionInfo(linkCode);
    
    // Get user profile to get full name and bio
    const userProfile = await api.getUser(subscriptionInfo.username);
    
    return {
      username: subscriptionInfo.username,
      fullName: userProfile?.full_name || subscriptionInfo.username,
      privacy_level: subscriptionInfo.privacy_level,
      bio: userProfile?.bio || `Updates from ${subscriptionInfo.username}`,
      available_frequencies: subscriptionInfo.available_frequencies
    };
  } catch (error) {
    console.error('Error fetching subscription info:', error);
    return null;
  }
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-pulse">
        <div className="h-8 bg-gray-200 rounded mb-4"></div>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

async function SubscribePageContent({ linkCode }: { linkCode: string }) {
  const subscriptionInfo = await getSubscriptionInfo(linkCode);

  if (!subscriptionInfo) {
    notFound();
  }

  const handleSubscribe = async (data: { email: string; frequency: string; name?: string }) => {
    'use server';
    
    try {
      const result = await api.subscribeToNewsletter({
        privacy_code: linkCode,
        subscriber_email: data.email,
        frequency: data.frequency,
        subscriber_name: data.name
      });
      
      return result;
    } catch (error) {
      console.error('Subscription error:', error);
      return { 
        success: false, 
        message: 'Failed to subscribe. Please try again.',
        subscription_id: '',
        unsubscribe_code: ''
      };
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* User Profile Preview */}
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <User className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold mb-2">{subscriptionInfo.fullName}</h1>
            <p className="text-gray-600 mb-4">{subscriptionInfo.bio}</p>
            <div className="flex items-center justify-center gap-2">
              <Mail className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-500">
                Subscribe to get updates from {subscriptionInfo.fullName}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Subscription Form */}
        <NewsletterSubscription
          linkCode={linkCode}
          username={subscriptionInfo.fullName}
          privacyLevel={subscriptionInfo.privacy_level}
          onSubscribe={handleSubscribe}
        />

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>
            Powered by <strong>HowYouBeen</strong> - AI-powered social connections
          </p>
          <p className="mt-1">
            <a href="https://howyoubeen.com" className="text-blue-600 hover:underline">
              Create your own profile
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default async function SubscribePage({ params }: SubscribePageProps) {
  const { linkCode } = await params;
  
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <SubscribePageContent linkCode={linkCode} />
    </Suspense>
  );
}
