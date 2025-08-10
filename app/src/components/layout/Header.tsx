'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface HeaderProps {
  user?: {
    username: string;
    full_name: string;
  } | null;
  onLogout?: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  const router = useRouter();

  return (
    <header className="bg-card/80 backdrop-blur-sm border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <nav className="flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-foreground hover:text-primary transition-colors">
            KeepInTouch
          </Link>
          
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Link 
                  href="/dashboard"
                  className="text-muted-foreground hover:text-primary transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  href={`/${user.username}`}
                  className="text-muted-foreground hover:text-primary transition-colors"
                >
                  My Profile
                </Link>
                <span className="text-muted-foreground">Hi, {user.full_name}</span>
                <Button variant="outline" size="sm" onClick={onLogout}>
                  Sign Out
                </Button>
              </>
            ) : (
              <>
                <Link 
                  href="/login"
                  className="text-muted-foreground hover:text-primary transition-colors"
                >
                  Sign In
                </Link>
                <Button onClick={() => router.push('/onboarding')}>
                  Get Started
                </Button>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
