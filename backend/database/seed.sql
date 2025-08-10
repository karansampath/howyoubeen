-- KeepInTouch Database Seed Data
-- Sample data for development and testing

-- Sample users (these will need actual auth.uid() values in production)
INSERT INTO users (id, username, email, full_name, bio, is_public, onboarding_completed) VALUES
(uuid_generate_v4(), 'johndoe', 'john@example.com', 'John Doe', 'Software engineer who loves hiking and reading', true, true),
(uuid_generate_v4(), 'janedoe', 'jane@example.com', 'Jane Doe', 'Product manager passionate about user experience', true, true),
(uuid_generate_v4(), 'alicesmith', 'alice@example.com', 'Alice Smith', 'Designer and photographer exploring the world', true, false)
ON CONFLICT (username) DO NOTHING;

-- Get user IDs for foreign key references
DO $$
DECLARE
    john_id UUID;
    jane_id UUID;
    alice_id UUID;
    vc_family_john UUID;
    vc_friends_john UUID;
    vc_family_jane UUID;
    doc_john UUID;
BEGIN
    SELECT id INTO john_id FROM users WHERE username = 'johndoe';
    SELECT id INTO jane_id FROM users WHERE username = 'janedoe';
    SELECT id INTO alice_id FROM users WHERE username = 'alicesmith';

    -- Sample visibility categories
    INSERT INTO visibility_categories (id, user_id, type, name) VALUES
    (uuid_generate_v4(), john_id, 'close_family', null),
    (uuid_generate_v4(), john_id, 'best_friends', null),
    (uuid_generate_v4(), john_id, 'good_friends', null),
    (uuid_generate_v4(), john_id, 'public', null),
    (uuid_generate_v4(), jane_id, 'close_family', null),
    (uuid_generate_v4(), jane_id, 'best_friends', null),
    (uuid_generate_v4(), jane_id, 'public', null),
    (uuid_generate_v4(), alice_id, 'best_friends', null),
    (uuid_generate_v4(), alice_id, 'public', null)
    ON CONFLICT DO NOTHING;

    -- Get visibility category IDs
    SELECT id INTO vc_family_john FROM visibility_categories WHERE user_id = john_id AND type = 'close_family';
    SELECT id INTO vc_friends_john FROM visibility_categories WHERE user_id = john_id AND type = 'best_friends';
    SELECT id INTO vc_family_jane FROM visibility_categories WHERE user_id = jane_id AND type = 'close_family';

    -- Sample info sources
    INSERT INTO info_sources (user_id, platform, url, info_description) VALUES
    (john_id, 'linkedin', 'https://linkedin.com/in/johndoe', 'Professional profile and network'),
    (john_id, 'github', 'https://github.com/johndoe', 'Code repositories and projects'),
    (jane_id, 'linkedin', 'https://linkedin.com/in/janedoe', 'Professional profile and network'),
    (jane_id, 'goodreads', 'https://goodreads.com/janedoe', 'Reading list and book reviews'),
    (alice_id, 'instagram', 'https://instagram.com/alicesmith', 'Photography and lifestyle updates')
    ON CONFLICT DO NOTHING;

    -- Sample documents
    INSERT INTO documents (id, user_id, file_path, content_type, description) VALUES
    (uuid_generate_v4(), john_id, 'user-documents/john/resume.pdf', 'document', 'Professional resume'),
    (uuid_generate_v4(), john_id, 'user-documents/john/hiking-photo.jpg', 'image', 'Recent hiking trip photo'),
    (uuid_generate_v4(), jane_id, 'user-documents/jane/portfolio.pdf', 'document', 'Design portfolio'),
    (uuid_generate_v4(), alice_id, 'user-documents/alice/travel-journal.txt', 'text', 'Travel experiences journal')
    ON CONFLICT DO NOTHING;

    -- Get document ID for associations
    SELECT id INTO doc_john FROM documents WHERE user_id = john_id AND content_type = 'document';

    -- Sample diary entries
    INSERT INTO diary_entries (user_id, visibility_category_id, start_date, summary) VALUES
    (john_id, vc_friends_john, now() - interval '7 days', 'Had an amazing weekend hiking in the mountains with friends. The weather was perfect and we discovered some beautiful trails.'),
    (john_id, vc_family_john, now() - interval '3 days', 'Celebrated Mom''s birthday with a family dinner. She loved the photo book we made for her.'),
    (jane_id, vc_family_jane, now() - interval '5 days', 'Finished reading "Design of Everyday Things" - such great insights for my current project.'),
    (jane_id, vc_friends_john, now() - interval '2 days', 'Launched the new feature at work! The team worked so hard and the user feedback has been fantastic.'),
    (alice_id, (SELECT id FROM visibility_categories WHERE user_id = alice_id AND type = 'public'), now() - interval '1 day', 'Currently onboarding but excited to share my photography adventures with friends!')
    ON CONFLICT DO NOTHING;

    -- Sample life facts
    INSERT INTO life_facts (user_id, visibility_category_id, summary, category) VALUES
    (john_id, (SELECT id FROM visibility_categories WHERE user_id = john_id AND type = 'public'), 'Professional skills: Python, JavaScript, System Design, Machine Learning', 'professional'),
    (john_id, vc_friends_john, 'Loves outdoor activities, especially hiking and rock climbing', 'interests'),
    (john_id, vc_family_john, 'Grew up in Colorado, moved to SF for work', 'background'),
    (jane_id, (SELECT id FROM visibility_categories WHERE user_id = jane_id AND type = 'public'), 'Experience: 8+ years in product management at tech startups', 'professional'),
    (jane_id, vc_friends_john, 'Avid reader, especially enjoys sci-fi and design books', 'interests'),
    (jane_id, vc_family_jane, 'Has two cats named Pixel and Vector', 'personal'),
    (alice_id, (SELECT id FROM visibility_categories WHERE user_id = alice_id AND type = 'public'), 'Professional photographer specializing in travel and landscape photography', 'professional')
    ON CONFLICT DO NOTHING;

    -- Sample friends relationships
    INSERT INTO friends (owner_user_id, friend_email, friend_name, visibility_category_id, relationship_context) VALUES
    (john_id, 'jane@example.com', 'Jane Doe', vc_friends_john, 'Former colleague, close friend'),
    (john_id, 'mom@example.com', 'Mom', vc_family_john, 'Family'),
    (john_id, 'college-friend@example.com', 'Mike Wilson', (SELECT id FROM visibility_categories WHERE user_id = john_id AND type = 'good_friends'), 'College roommate'),
    (jane_id, 'john@example.com', 'John Doe', (SELECT id FROM visibility_categories WHERE user_id = jane_id AND type = 'best_friends'), 'Former colleague, close friend'),
    (jane_id, 'sister@example.com', 'Sarah', vc_family_jane, 'Sister')
    ON CONFLICT DO NOTHING;

    -- Sample conversations
    INSERT INTO conversations (profile_username, friend_identifier, messages) VALUES
    ('johndoe', 'jane@example.com', '[
        {
            "role": "friend",
            "content": "Hey John! How was your weekend?",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "role": "ai",
            "content": "Hi Jane! I had an amazing weekend hiking in the mountains with friends. The weather was perfect and we discovered some beautiful new trails. How was your weekend?",
            "timestamp": "2024-01-15T10:02:00Z"
        },
        {
            "role": "friend", 
            "content": "That sounds awesome! I spent the weekend reading and working on a new design project. Any photos from the hike?",
            "timestamp": "2024-01-15T10:05:00Z"
        }
    ]'::jsonb),
    ('janedoe', 'anonymous_visitor', '[
        {
            "role": "friend",
            "content": "What''s Jane been up to lately?",
            "timestamp": "2024-01-16T14:00:00Z"
        },
        {
            "role": "ai",
            "content": "Jane recently launched a new feature at work and the team received fantastic user feedback! She''s also been reading \"Design of Everyday Things\" which provided great insights for her current project.",
            "timestamp": "2024-01-16T14:01:00Z"
        }
    ]'::jsonb)
    ON CONFLICT DO NOTHING;

    -- Link documents to diary entries and life facts
    INSERT INTO diary_entry_documents (diary_entry_id, document_id)
    SELECT de.id, doc_john
    FROM diary_entries de
    WHERE de.user_id = john_id AND de.summary LIKE '%hiking%'
    ON CONFLICT DO NOTHING;

    INSERT INTO life_fact_documents (life_fact_id, document_id)
    SELECT lf.id, doc_john
    FROM life_facts lf
    WHERE lf.user_id = john_id AND lf.category = 'professional'
    ON CONFLICT DO NOTHING;

END $$;