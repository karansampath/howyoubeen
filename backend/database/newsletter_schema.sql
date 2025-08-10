-- Newsletter Subscription Schema Extension
-- This extends the main schema with newsletter subscription functionality

-- Newsletter subscriptions table
CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  source_username TEXT NOT NULL,
  subscriber_email TEXT NOT NULL,
  privacy_level TEXT NOT NULL CHECK (privacy_level IN ('close_family', 'best_friends', 'good_friends', 'acquaintances', 'public')),
  frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'unsubscribed')),
  subscription_code UUID NOT NULL DEFAULT uuid_generate_v4(),
  last_sent TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  -- Ensure one subscription per email/user/privacy_level combination
  UNIQUE(source_user_id, subscriber_email, privacy_level)
);

-- Newsletter delivery log for tracking
CREATE TABLE IF NOT EXISTS newsletter_delivery_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subscription_id UUID REFERENCES newsletter_subscriptions(id) ON DELETE CASCADE,
  sent_at TIMESTAMPTZ DEFAULT now(),
  status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'bounced')),
  error_message TEXT,
  content_preview TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Privacy level links table (for generating subscription links with codes)
CREATE TABLE IF NOT EXISTS privacy_level_links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  privacy_level TEXT NOT NULL CHECK (privacy_level IN ('close_family', 'best_friends', 'good_friends', 'acquaintances', 'public')),
  link_code UUID NOT NULL DEFAULT uuid_generate_v4(),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  
  -- One active link per user per privacy level
  UNIQUE(user_id, privacy_level)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_newsletter_subscriptions_source_user_id ON newsletter_subscriptions(source_user_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscriptions_subscriber_email ON newsletter_subscriptions(subscriber_email);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscriptions_status ON newsletter_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscriptions_frequency ON newsletter_subscriptions(frequency);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscriptions_last_sent ON newsletter_subscriptions(last_sent);
CREATE INDEX IF NOT EXISTS idx_newsletter_delivery_log_subscription_id ON newsletter_delivery_log(subscription_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_delivery_log_sent_at ON newsletter_delivery_log(sent_at);
CREATE INDEX IF NOT EXISTS idx_privacy_level_links_user_id ON privacy_level_links(user_id);
CREATE INDEX IF NOT EXISTS idx_privacy_level_links_link_code ON privacy_level_links(link_code);

-- Trigger for updated_at on newsletter_subscriptions
CREATE TRIGGER update_newsletter_subscriptions_updated_at BEFORE UPDATE ON newsletter_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE newsletter_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletter_delivery_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE privacy_level_links ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can manage subscriptions to their own newsletters
CREATE POLICY "Users can manage their newsletter subscriptions" ON newsletter_subscriptions
  FOR ALL USING (auth.uid() = source_user_id::text::uuid);

-- Anyone can subscribe (for public endpoints), but can only unsubscribe their own
CREATE POLICY "Anyone can subscribe to newsletters" ON newsletter_subscriptions
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Subscribers can unsubscribe themselves" ON newsletter_subscriptions
  FOR UPDATE USING (true);  -- Will be controlled by application logic using subscription_code

-- Users can view delivery logs for their newsletters
CREATE POLICY "Users can view their newsletter delivery logs" ON newsletter_delivery_log
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM newsletter_subscriptions ns 
      WHERE ns.id = newsletter_delivery_log.subscription_id 
      AND auth.uid() = ns.source_user_id::text::uuid
    )
  );

-- Users can manage their privacy level links
CREATE POLICY "Users can manage their privacy level links" ON privacy_level_links
  FOR ALL USING (auth.uid() = user_id::text::uuid);
