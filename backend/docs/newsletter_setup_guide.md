# Newsletter Service Setup Guide

This guide will help you set up the complete newsletter functionality for the HowYouBeen platform.

## 🎯 Overview

The newsletter service allows friends to subscribe to personalized updates from users at different privacy levels (close family, best friends, good friends, acquaintances, public) with configurable frequency (daily, weekly, monthly).

### Architecture Components

1. **Database Schema** - Extended schema for subscriptions and privacy links
2. **Backend API** - Subscription management endpoints
3. **Newsletter Service** - Content generation and email sending
4. **Modal Cron Jobs** - Automated scheduled sending
5. **Frontend Components** - Subscription and management UI
6. **Mock Data** - Testing and demonstration

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL or Supabase
- Modal account (for cron jobs)
- SMTP email service (Gmail recommended)

## 🚀 Quick Start

### 1. Database Setup

Apply the newsletter schema extension:

```sql
-- Run this against your existing database
\i backend/database/newsletter_schema.sql
```

This adds:
- `newsletter_subscriptions` table
- `newsletter_delivery_log` table  
- `privacy_level_links` table
- Indexes and RLS policies

### 2. Environment Variables

Add to your `.env` file:

```bash
# Newsletter Email Configuration
NEWSLETTER_EMAIL=your-newsletter@gmail.com
NEWSLETTER_PASSWORD=your-app-password
NEWSLETTER_NAME="HowYouBeen"

# Modal Configuration (for cron jobs)
NEWSLETTER_API_URL=https://your-api-domain.com
NEWSLETTER_API_KEY=your-optional-api-key
```

### 3. Backend Dependencies

Install additional Python packages:

```bash
cd backend
pip install -r requirements.txt

# If not already included, add:
pip install smtplib-ssl email-mime
```

### 4. Frontend Dependencies

No additional dependencies needed - uses existing UI components.

### 5. Test the Implementation

Run the demo script:

```bash
cd backend/src/howyoubeen
python demo_newsletter.py
```

## 🔧 Detailed Setup

### Database Configuration

The newsletter system extends your existing database with three new tables:

#### newsletter_subscriptions
- Stores all newsletter subscriptions
- Links subscribers to users with privacy levels
- Tracks frequency and status

#### newsletter_delivery_log  
- Logs all newsletter delivery attempts
- Tracks success/failure for monitoring

#### privacy_level_links
- Maps privacy codes to users and privacy levels
- Enables shareable subscription links

### API Integration

Add newsletter routes to your FastAPI server:

```python
# In your main.py
from howyoubeen.server.routes.newsletter import router as newsletter_router

app.include_router(newsletter_router)
```

### Modal Cron Job Deployment

1. Install Modal CLI:
```bash
pip install modal
```

2. Set up Modal secrets:
```bash
modal secret create NEWSLETTER_API_URL
modal secret create NEWSLETTER_API_KEY
```

3. Deploy the cron jobs:
```bash
modal deploy backend/src/howyoubeen/modal_newsletter_cron.py
```

### Email Configuration

For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password as `NEWSLETTER_PASSWORD`

### Frontend Integration

Add newsletter components to your app:

```tsx
// For user dashboard
import NewsletterManager from '@/components/newsletter/NewsletterManager';

// For subscription pages
import NewsletterSubscription from '@/components/newsletter/NewsletterSubscription';
```

## 📊 Usage Examples

### Creating Subscription Links

```python
# Generate a privacy-level specific link
link = await newsletter_service.create_subscription_link(
    user_id="user-123",
    privacy_level=VisibilityCategoryType.BEST_FRIENDS
)
# Returns: https://howyoubeen.com/subscribe/bf-user-abc123
```

### Processing Subscriptions

```python
# When someone subscribes via link
result = await newsletter_service.subscribe_to_newsletter(
    privacy_code="bf-user-abc123",
    subscriber_email="friend@example.com",
    frequency=NewsletterFrequency.WEEKLY
)
```

### Sending Newsletters

```python
# Send all daily newsletters (called by cron)
result = await newsletter_service.send_newsletters_by_frequency(
    NewsletterFrequency.DAILY
)
```

## 🔄 Newsletter Flow

### Subscription Process
1. User creates privacy-level links in dashboard
2. User shares links with friends/family
3. Friend clicks link → subscription page
4. Friend enters email and frequency → subscribed
5. System stores subscription with privacy level

### Newsletter Generation
1. Cron job triggers at scheduled times
2. System finds active subscriptions for frequency
3. For each subscription:
   - Gets user's recent content for privacy level
   - Generates personalized newsletter
   - Sends email with unsubscribe link
   - Logs delivery status

### Content Privacy
- Diary entries and life facts have visibility categories
- Newsletter shows only content matching subscriber's privacy level
- AI can generate contextual summaries

## 📈 Monitoring

### Delivery Logs
Monitor newsletter delivery in the `newsletter_delivery_log` table:

```sql
SELECT 
  ns.source_username,
  ns.subscriber_email,
  ndl.status,
  ndl.sent_at,
  ndl.error_message
FROM newsletter_delivery_log ndl
JOIN newsletter_subscriptions ns ON ndl.subscription_id = ns.id
WHERE ndl.sent_at >= NOW() - INTERVAL '24 hours'
ORDER BY ndl.sent_at DESC;
```

### Subscription Stats
```sql
SELECT 
  frequency,
  privacy_level,
  status,
  COUNT(*) as count
FROM newsletter_subscriptions 
GROUP BY frequency, privacy_level, status;
```

## 🧪 Testing

### Mock Data Testing
```bash
# Run demo with mock data
python backend/src/howyoubeen/demo_newsletter.py

# Test specific functionality
python backend/src/howyoubeen/lib/newsletter_mock_data.py
```

### Manual Testing
```bash
# Test cron job manually
modal run modal_newsletter_cron.py::send_newsletters_manually --frequency daily

# Test subscription API
curl -X POST http://localhost:8000/newsletter/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "privacy_code": "test-code",
    "subscriber_email": "test@example.com",
    "frequency": "weekly"
  }'
```

## 🚦 Production Deployment

### Security Considerations
1. **API Authentication**: Add API key validation to admin endpoints
2. **Rate Limiting**: Implement rate limits on subscription endpoints
3. **Email Validation**: Validate email addresses before subscribing
4. **Unsubscribe Protection**: Validate subscription codes

### Performance Optimization
1. **Batch Processing**: Process newsletters in batches
2. **Content Caching**: Cache generated content for similar privacy levels
3. **Database Indexing**: Ensure proper indexes on subscription queries
4. **Email Throttling**: Respect SMTP rate limits

### Monitoring in Production
1. **Delivery Success Rate**: Monitor bounce/failure rates
2. **Subscription Growth**: Track subscription metrics
3. **Performance**: Monitor newsletter generation time
4. **Error Alerts**: Set up alerts for failed deliveries

## ❓ Troubleshooting

### Common Issues

**Newsletter not sending**
- Check SMTP credentials
- Verify Modal cron job is deployed
- Check API endpoint accessibility

**Subscription links not working**
- Verify privacy_level_links table has data
- Check link code format
- Ensure frontend routes are configured

**Content not showing**
- Check privacy level matching
- Verify diary entries have correct visibility
- Check date ranges for content filtering

### Debug Mode
Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### Subscription Endpoints
- `POST /newsletter/subscribe` - Subscribe to newsletter
- `POST /newsletter/unsubscribe` - Unsubscribe from newsletter
- `GET /newsletter/subscriptions/{user_id}` - Get user's subscribers

### Admin Endpoints (Cron)
- `POST /newsletter/admin/send-daily` - Send daily newsletters
- `POST /newsletter/admin/send-weekly` - Send weekly newsletters  
- `POST /newsletter/admin/send-monthly` - Send monthly newsletters

### Management Endpoints
- `POST /newsletter/create-link` - Create subscription link
- `GET /newsletter/link/{link_code}` - Get link information

## 🎉 Success!

Your newsletter service is now ready! Users can:
- ✅ Create privacy-level specific subscription links
- ✅ Share links with friends and family
- ✅ Receive automated newsletters based on privacy level
- ✅ Manage their subscriptions
- ✅ Unsubscribe easily

The system automatically handles content generation, email formatting, and scheduled delivery through Modal cron jobs.
