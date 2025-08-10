import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import NewsletterSubscription from '@/components/newsletter/NewsletterSubscription';
import { Card, CardContent } from '@/components/ui/card';
import { Mail, User } from 'lucide-react';

interface SubscribePageProps {
  params: {
    linkCode: string;
  };
}

// Mock function - replace with actual API call
async function getSubscriptionInfo(linkCode: string) {
  // In a real app, this would call your API
  const mockData = {
    'bf-sarah-abc123': {
      username: 'sarah_codes',
      fullName: 'Sarah Johnson',
      privacy_level: 'best_friends',
      bio: 'Full-stack developer, AI enthusiast, and coffee connoisseur ☕'
    },
    'gf-sarah-def456': {
      username: 'sarah_codes',
      fullName: 'Sarah Johnson', 
      privacy_level: 'good_friends',
      bio: 'Full-stack developer, AI enthusiast, and coffee connoisseur ☕'
    },
    'public-sarah-ghi789': {
      username: 'sarah_codes',
      fullName: 'Sarah Johnson',
      privacy_level: 'public',
      bio: 'Full-stack developer, AI enthusiast, and coffee connoisseur ☕'
    },
    'bf-mike-jkl012': {
      username: 'world_wanderer_mike',
      fullName: 'Mike Chen',
      privacy_level: 'best_friends', 
      bio: 'Digital nomad documenting adventures around the globe 🌍'
    },
    'public-mike-mno345': {
      username: 'world_wanderer_mike',
      fullName: 'Mike Chen',
      privacy_level: 'public',
      bio: 'Digital nomad documenting adventures around the globe 🌍'
    },
    'family-emma-pqr678': {
      username: 'family_life_emma',
      fullName: 'Emma Rodriguez',
      privacy_level: 'close_family',
      bio: 'New mom, marketing professional, and advocate for work-life balance 👶'
    },
    'gf-emma-stu901': {
      username: 'family_life_emma',
      fullName: 'Emma Rodriguez',
      privacy_level: 'good_friends',
      bio: 'New mom, marketing professional, and advocate for work-life balance 👶'
    }
  };

  return mockData[linkCode as keyof typeof mockData] || null;
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
    
    // In a real implementation, this would call your API
    console.log('Subscription data:', {
      privacy_code: linkCode,
      subscriber_email: data.email,
      frequency: data.frequency,
      subscriber_name: data.name
    });
    
    // Mock successful subscription
    return { success: true };
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

export default function SubscribePage({ params }: SubscribePageProps) {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <SubscribePageContent linkCode={params.linkCode} />
    </Suspense>
  );
}

// Generate static paths for common link codes (optional optimization)
export async function generateStaticParams() {
  // In a real app, you might generate this from your database
  const commonLinkCodes = [
    'bf-sarah-abc123',
    'gf-sarah-def456', 
    'public-sarah-ghi789',
    'bf-mike-jkl012',
    'public-mike-mno345',
    'family-emma-pqr678',
    'gf-emma-stu901'
  ];

  return commonLinkCodes.map((linkCode) => ({
    linkCode,
  }));
}
