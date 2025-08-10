-- KeepInTouch Database Schema for Supabase
-- This file contains the complete database schema for the KeepInTouch application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table - Core user information
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  bio TEXT,
  profile_image_url TEXT,
  is_public BOOLEAN DEFAULT true,
  onboarding_completed BOOLEAN DEFAULT false,
  knowledge_last_updated TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Visibility categories - Replaces enum with relational table
CREATE TABLE IF NOT EXISTS visibility_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('close_family', 'best_friends', 'good_friends', 'acquaintances', 'public', 'private', 'custom')),
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, type, name)
);

-- Info sources - External data sources (LinkedIn, GitHub, etc.)
CREATE TABLE IF NOT EXISTS info_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  url TEXT,
  info_description TEXT NOT NULL,
  last_checked TIMESTAMPTZ DEFAULT now(),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Documents - File metadata and references
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  file_path TEXT, -- Supabase Storage path
  url TEXT, -- External URL if applicable
  content_type TEXT NOT NULL CHECK (content_type IN ('text', 'image', 'video', 'link', 'audio', 'document')),
  description TEXT,
  file_size BIGINT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Diary entries - Time-based life updates
CREATE TABLE IF NOT EXISTS diary_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  visibility_category_id UUID REFERENCES visibility_categories(id) ON DELETE SET NULL,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ,
  summary TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Life facts - Timeless personal information
CREATE TABLE IF NOT EXISTS life_facts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  visibility_category_id UUID REFERENCES visibility_categories(id) ON DELETE SET NULL,
  summary TEXT NOT NULL,
  category TEXT, -- professional, interests, values, etc.
  date TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Friends/relationships - User connections
CREATE TABLE IF NOT EXISTS friends (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  friend_email TEXT NOT NULL,
  friend_name TEXT NOT NULL,
  visibility_category_id UUID REFERENCES visibility_categories(id) ON DELETE SET NULL,
  relationship_context TEXT,
  newsletter_subscribed BOOLEAN DEFAULT false,
  added_at TIMESTAMPTZ DEFAULT now(),
  last_interaction TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true
);

-- Conversations - Chat sessions with friends
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_username TEXT NOT NULL,
  friend_identifier TEXT, -- email or session identifier
  messages JSONB DEFAULT '[]', -- Array of message objects
  created_at TIMESTAMPTZ DEFAULT now(),
  last_message_at TIMESTAMPTZ DEFAULT now(),
  is_active BOOLEAN DEFAULT true
);

-- Onboarding sessions - Temporary session data
CREATE TABLE IF NOT EXISTS onboarding_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID, -- May be null until user is created
  step TEXT NOT NULL,
  data JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Junction table for diary entries and documents
CREATE TABLE IF NOT EXISTS diary_entry_documents (
  diary_entry_id UUID REFERENCES diary_entries(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  PRIMARY KEY (diary_entry_id, document_id)
);

-- Junction table for life facts and documents
CREATE TABLE IF NOT EXISTS life_fact_documents (
  life_fact_id UUID REFERENCES life_facts(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  PRIMARY KEY (life_fact_id, document_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_visibility_categories_user_id ON visibility_categories(user_id);
CREATE INDEX IF NOT EXISTS idx_info_sources_user_id ON info_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_diary_entries_user_id ON diary_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_life_facts_user_id ON life_facts(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_owner_user_id ON friends(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_friends_friend_email ON friends(friend_email);
CREATE INDEX IF NOT EXISTS idx_conversations_profile_username ON conversations(profile_username);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_user_id ON onboarding_sessions(user_id);

-- Functions for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diary_entries_updated_at BEFORE UPDATE ON diary_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_life_facts_updated_at BEFORE UPDATE ON life_facts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_onboarding_sessions_updated_at BEFORE UPDATE ON onboarding_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE visibility_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE info_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE diary_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE friends ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (can be refined based on requirements)
-- Users can read/write their own data
CREATE POLICY "Users can manage their own data" ON users
  FOR ALL USING (auth.uid() = id::text::uuid);

CREATE POLICY "Users can manage their visibility categories" ON visibility_categories
  FOR ALL USING (auth.uid() = user_id::text::uuid);

CREATE POLICY "Users can manage their info sources" ON info_sources
  FOR ALL USING (auth.uid() = user_id::text::uuid);

CREATE POLICY "Users can manage their documents" ON documents
  FOR ALL USING (auth.uid() = user_id::text::uuid);

CREATE POLICY "Users can manage their diary entries" ON diary_entries
  FOR ALL USING (auth.uid() = user_id::text::uuid);

CREATE POLICY "Users can manage their life facts" ON life_facts
  FOR ALL USING (auth.uid() = user_id::text::uuid);

CREATE POLICY "Users can manage their friends" ON friends
  FOR ALL USING (auth.uid() = owner_user_id::text::uuid);

-- Conversations - more complex policy for friend access
CREATE POLICY "Users can access conversations about their profile" ON conversations
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE username = conversations.profile_username 
      AND auth.uid() = users.id::text::uuid
    )
  );

-- Onboarding sessions - users can access their own sessions
CREATE POLICY "Users can manage their onboarding sessions" ON onboarding_sessions
  FOR ALL USING (auth.uid() = user_id::text::uuid);

-- Public profiles can be read by anyone
CREATE POLICY "Public profiles are readable" ON users
  FOR SELECT USING (is_public = true);

-- Storage bucket policies (to be created in Supabase Storage)
-- These policies will be created through the Supabase dashboard
-- Bucket: user-documents
-- Policy: Users can upload to their own folder
-- Policy: Users can read their own files