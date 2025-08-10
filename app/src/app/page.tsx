import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-border">
      {/* Header */}
      <header className="container mx-auto px-6 py-8">
        <nav className="flex justify-between items-center">
          <div className="text-2xl font-bold text-foreground">
            KeepInTouch
          </div>
          <div className="flex gap-4">
            <Link 
              href="/login"
              className="px-4 py-2 text-muted-foreground hover:text-primary transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/onboarding"
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-accent transition-colors"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
            Meaningful Friendships
            <br />
            <span className="text-primary">Through AI</span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
            Stay connected with friends through AI-powered personal profiles. 
            Share your life updates and let your AI help friends stay in touch 
            without competing for attention.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              href="/onboarding"
              className="px-8 py-4 bg-primary text-primary-foreground text-lg font-semibold rounded-xl hover:bg-accent transition-colors shadow-lg"
            >
              Create Your Profile
            </Link>
            <Link
              href="#demo"
              className="px-8 py-4 border-2 border-primary text-primary text-lg font-semibold rounded-xl hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              See How It Works
            </Link>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-8 mt-20">
            <div className="bg-card/60 backdrop-blur-sm p-8 rounded-2xl border border-border hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mb-6 mx-auto">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                AI-Powered Profiles
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                Your personal AI learns about your life and shares updates 
                with friends based on your privacy preferences.
              </p>
            </div>

            <div className="bg-card/60 backdrop-blur-sm p-8 rounded-2xl border border-border hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-secondary rounded-2xl flex items-center justify-center mb-6 mx-auto">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                Privacy Control
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                Configure friendship tiers and control exactly what 
                information each friend level can access.
              </p>
            </div>

            <div className="bg-card/60 backdrop-blur-sm p-8 rounded-2xl border border-border hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-accent rounded-2xl flex items-center justify-center mb-6 mx-auto">
                <span className="text-2xl">💬</span>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                Natural Conversations
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                Friends can chat naturally with your AI to stay updated 
                without needing your direct attention.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Demo Section */}
      <section id="demo" className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-foreground mb-12">
            How It Works
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-semibold text-foreground mb-4">
                For You (Person A)
              </h3>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">1.</span>
                  Complete AI-guided onboarding interview
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">2.</span>
                  Connect data sources (LinkedIn, GitHub, Instagram)
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">3.</span>
                  Configure friendship tiers and privacy levels
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold">4.</span>
                  Upload life updates and manage your AI
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-2xl font-semibold text-foreground mb-4">
                For Your Friends
              </h3>
              <ul className="space-y-3 text-muted-foreground">
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">1.</span>
                  Visit your unique profile URL
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">2.</span>
                  Chat naturally with your AI assistant
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">3.</span>
                  Get updates based on friendship level
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-secondary font-bold">4.</span>
                  Subscribe to newsletters for regular updates
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-foreground text-background py-12">
        <div className="container mx-auto px-6 text-center">
          <div className="text-2xl font-bold mb-4">KeepInTouch</div>
          <p className="text-muted mb-6">
            Maintaining meaningful friendships through AI-powered connections
          </p>
          <div className="flex justify-center gap-8">
            <Link href="/privacy" className="hover:text-primary transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-primary transition-colors">Terms</Link>
            <Link href="/contact" className="hover:text-primary transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
