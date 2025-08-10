'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { api, type OnboardingDataRequest } from '@/lib/api';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
}

const steps: OnboardingStep[] = [
  { id: 'basic', title: 'Basic Information', description: 'Tell us about yourself' },
  { id: 'sources', title: 'Data Sources', description: 'Connect your accounts' },
  { id: 'privacy', title: 'Newsletter Settings', description: 'Configure privacy levels for subscribers' },
  { id: 'review', title: 'Review & Launch', description: 'Start your newsletter' }
];

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Form data
  const [basicInfo, setBasicInfo] = useState({
    fullName: '',
    username: '',
    email: '',
    bio: ''
  });
  
  const [error, setError] = useState<string | null>(null);
  
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  
  const friendshipTiers = [
    { name: 'Close Family', level: 'close_family', description: 'Immediate family members' },
    { name: 'Best Friends', level: 'best_friends', description: 'Closest friends' },
    { name: 'Good Friends', level: 'good_friends', description: 'Regular friends' },
    { name: 'Acquaintances', level: 'acquaintances', description: 'Colleagues and casual friends' }
  ];

  const dataSources = [
    { id: 'linkedin', name: 'LinkedIn', description: 'Professional profile and connections' },
    { id: 'github', name: 'GitHub', description: 'Code repositories and projects' },
    { id: 'instagram', name: 'Instagram', description: 'Photos and social updates' },
    { id: 'goodreads', name: 'Goodreads', description: 'Reading list and book reviews' },
    { id: 'google_photos', name: 'Google Photos', description: 'Photos and memories' }
  ];

  const handleNext = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (currentStep === 0) {
        // Start onboarding session if needed
        if (!sessionId) {
          const session = await api.startOnboarding();
          setSessionId(session.session_id);
        }
      }
      
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        // Final step - complete onboarding
        if (!sessionId) {
          throw new Error('No session ID available');
        }
        
        const onboardingData: OnboardingDataRequest = {
          username: basicInfo.username,
          email: basicInfo.email,
          bio: basicInfo.bio,
          data_sources: selectedSources,
          visibility_preference: 'friends_only', // Default visibility
        };
        
        const result = await api.submitOnboardingData(sessionId, onboardingData);
        
        // Redirect to user profile or dashboard
        window.location.href = `/dashboard?user=${result.username}`;
      }
    } catch (error) {
      console.error('Error in onboarding step:', error);
      setError(error instanceof Error ? error.message : 'An error occurred during onboarding');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return basicInfo.fullName && basicInfo.username && basicInfo.email && basicInfo.bio;
      case 1:
        return selectedSources.length > 0;
      case 2:
        return true; // Privacy settings are optional with defaults
      case 3:
        return true; // Review step
      default:
        return false;
    }
  };

  const toggleDataSource = (sourceId: string) => {
    setSelectedSources(prev => 
      prev.includes(sourceId) 
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Progress Header */}
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-center text-foreground mb-8">
              Set Up Your Newsletter
            </h1>
            
            <div className="flex justify-center mb-8">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    index <= currentStep 
                      ? 'bg-primary border-primary text-primary-foreground' 
                      : 'border-border text-muted-foreground'
                  }`}>
                    {index + 1}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-1 mx-2 ${
                      index < currentStep ? 'bg-primary' : 'bg-border'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-foreground">
                {steps[currentStep].title}
              </h2>
              <p className="text-muted-foreground mt-2">
                {steps[currentStep].description}
              </p>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Step Content */}
          <Card className="mb-8">
            <CardContent className="p-8">
              {currentStep === 0 && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <Input
                      label="Full Name"
                      placeholder="John Doe"
                      value={basicInfo.fullName}
                      onChange={(e) => setBasicInfo({...basicInfo, fullName: e.target.value})}
                      required
                    />
                    <Input
                      label="Username"
                      placeholder="johndoe"
                      value={basicInfo.username}
                      onChange={(e) => setBasicInfo({...basicInfo, username: e.target.value})}
                      required
                    />
                  </div>
                  
                  <Input
                    label="Email"
                    type="email"
                    placeholder="john@example.com"
                    value={basicInfo.email}
                    onChange={(e) => setBasicInfo({...basicInfo, email: e.target.value})}
                    required
                  />
                  
                  <Textarea
                    label="Bio"
                    placeholder="Tell us about yourself, your interests, and what you'd like to share in your newsletters..."
                    value={basicInfo.bio}
                    onChange={(e) => setBasicInfo({...basicInfo, bio: e.target.value})}
                    rows={4}
                    required
                  />
                  
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      Your AI will use this information to understand your personality and create personalized newsletter content for different subscriber groups.
                    </p>
                  </div>
                </div>
              )}

              {currentStep === 1 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <p className="text-muted-foreground">
                      Select the accounts you&apos;d like to connect. Your AI will learn from these sources to create engaging newsletter content about &quot;how you been.&quot;
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    {dataSources.map((source) => (
                      <Card 
                        key={source.id}
                        className={`cursor-pointer transition-all ${
                          selectedSources.includes(source.id) 
                            ? 'ring-2 ring-primary bg-primary/5' 
                            : 'hover:bg-muted/50'
                        }`}
                        onClick={() => toggleDataSource(source.id)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="font-semibold text-foreground">{source.name}</h3>
                              <p className="text-sm text-muted-foreground">{source.description}</p>
                            </div>
                            <div className={`w-6 h-6 rounded-full border-2 ${
                              selectedSources.includes(source.id)
                                ? 'bg-primary border-primary' 
                                : 'border-border'
                            }`}>
                              {selectedSources.includes(source.id) && (
                                <div className="w-full h-full flex items-center justify-center">
                                  <span className="text-primary-foreground text-sm">✓</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                  
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      Selected: {selectedSources.length} source{selectedSources.length !== 1 ? 's' : ''}. 
                      You can always add or remove sources later from your dashboard.
                    </p>
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <p className="text-muted-foreground">
                      Configure privacy levels for your newsletter subscribers. Each group will receive content appropriate to your relationship with them.
                    </p>
                  </div>
                  
                  <div className="space-y-4">
                    {friendshipTiers.map((tier, index) => (
                      <Card key={tier.level}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <Badge variant="outline">{tier.name}</Badge>
                                <span className="text-sm text-muted-foreground">Level {index + 1}</span>
                              </div>
                              <p className="text-sm text-muted-foreground">{tier.description}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                  
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      These are default subscriber privacy levels. Each level will get different newsletter subscription links, so you can share appropriate content with each group.
                    </p>
                  </div>
                </div>
              )}

              {currentStep === 3 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      Your newsletter is ready!
                    </h3>
                    <p className="text-muted-foreground">
                      Review your settings and launch your personalized newsletter service.
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Profile Information</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <p><strong>Name:</strong> {basicInfo.fullName}</p>
                          <p><strong>Username:</strong> {basicInfo.username}</p>
                          <p><strong>Email:</strong> {basicInfo.email}</p>
                          <p><strong>Bio:</strong> {basicInfo.bio.substring(0, 100)}...</p>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle>Connected Sources</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {selectedSources.map(sourceId => {
                            const source = dataSources.find(s => s.id === sourceId);
                            return (
                              <Badge key={sourceId} variant="secondary">
                                {source?.name}
                              </Badge>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  
                  <div className="bg-primary/10 border border-primary/20 p-4 rounded-lg">
                    <p className="text-sm text-foreground">
                      <strong>Next steps:</strong> Your AI will process your information and create personalized newsletter content. 
                      You&apos;ll be able to create subscription links for different privacy levels and start sharing &quot;how you been&quot; with friends and family!
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button 
              variant="outline" 
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              Back
            </Button>
            
            <Button 
              onClick={handleNext}
              disabled={!canProceed() || isLoading}
            >
              {isLoading ? 'Processing...' : currentStep === steps.length - 1 ? 'Launch Newsletter' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
