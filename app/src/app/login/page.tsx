'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import Link from 'next/link';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate login - in real app, authenticate with backend
    setTimeout(() => {
      console.log('Login attempt:', formData);
      // For demo, redirect to dashboard
      window.location.href = '/dashboard';
    }, 1000);
  };

  const handleDemoLogin = () => {
    setIsLoading(true);
    // Direct login for demo purposes
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border flex items-center justify-center">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-md mx-auto">
          
          {/* Logo/Brand */}
          <div className="text-center mb-8">
            <Link href="/" className="text-3xl font-bold text-foreground hover:text-primary transition-colors">
              KeepInTouch
            </Link>
            <p className="text-muted-foreground mt-2">Sign in to your account</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-center">Welcome Back</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <Input
                  label="Email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
                
                <Input
                  label="Password"
                  type="password"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />

                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>

              <div className="mt-6">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-card text-muted-foreground">Or for demo</span>
                  </div>
                </div>

                <Button 
                  variant="outline" 
                  className="w-full mt-4"
                  onClick={handleDemoLogin}
                  disabled={isLoading}
                >
                  Continue as Demo User
                </Button>
              </div>

              <div className="mt-6 text-center space-y-2">
                <p className="text-sm text-muted-foreground">
                  Don&apos;t have an account?{' '}
                  <Link href="/onboarding" className="text-primary hover:underline">
                    Get started
                  </Link>
                </p>
                <p className="text-sm text-muted-foreground">
                  <Link href="/forgot-password" className="text-primary hover:underline">
                    Forgot your password?
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Demo Info */}
          <Card className="mt-6">
            <CardContent className="p-4">
              <h3 className="font-medium text-foreground mb-2">Demo Information</h3>
              <p className="text-sm text-muted-foreground mb-3">
                This is a demo version. You can:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Use &quot;Continue as Demo User&quot; to access the dashboard</li>
                <li>• Visit <code className="bg-muted px-1 rounded">localhost:3000/johndoe</code> to see the friend interface</li>
                <li>• Try the onboarding flow to see the setup process</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
