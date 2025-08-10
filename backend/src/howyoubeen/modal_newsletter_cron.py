"""Modal cron job for sending newsletters automatically"""

import modal
import requests
import os
from datetime import datetime
import logging

# Create Modal app
app = modal.App("howyoubeen-newsletter-cron")

# Define the image with required dependencies
image = modal.Image.debian_slim().pip_install([
    "requests>=2.31.0",
    "python-dotenv>=1.0.0"
])

# Environment variables for the service
newsletter_api_url = modal.Secret.from_name("NEWSLETTER_API_URL")  # Your backend API URL
newsletter_api_key = modal.Secret.from_name("NEWSLETTER_API_KEY")  # Optional API key for security


@app.function(
    image=image,
    schedule=modal.Cron("0 8 * * *"),  # Daily at 8 AM UTC
    secrets=[newsletter_api_url, newsletter_api_key]
)
def send_daily_newsletters():
    """Send daily newsletters - runs every day at 8 AM UTC"""
    
    api_url = os.environ.get("NEWSLETTER_API_URL", "http://localhost:8000")
    api_key = os.environ.get("NEWSLETTER_API_KEY")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(
            f"{api_url}/newsletter/admin/send-daily",
            headers=headers,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Daily newsletters sent successfully: {result}")
            return result
        else:
            error_msg = f"❌ Failed to send daily newsletters: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Error sending daily newsletters: {str(e)}"
        print(error_msg)
        raise


@app.function(
    image=image,
    schedule=modal.Cron("0 9 * * 1"),  # Weekly on Mondays at 9 AM UTC
    secrets=[newsletter_api_url, newsletter_api_key]
)
def send_weekly_newsletters():
    """Send weekly newsletters - runs every Monday at 9 AM UTC"""
    
    api_url = os.environ.get("NEWSLETTER_API_URL", "http://localhost:8000")
    api_key = os.environ.get("NEWSLETTER_API_KEY")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(
            f"{api_url}/newsletter/admin/send-weekly",
            headers=headers,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Weekly newsletters sent successfully: {result}")
            return result
        else:
            error_msg = f"❌ Failed to send weekly newsletters: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Error sending weekly newsletters: {str(e)}"
        print(error_msg)
        raise


@app.function(
    image=image,
    schedule=modal.Cron("0 10 1 * *"),  # Monthly on the 1st at 10 AM UTC
    secrets=[newsletter_api_url, newsletter_api_key]
)
def send_monthly_newsletters():
    """Send monthly newsletters - runs on the 1st of every month at 10 AM UTC"""
    
    api_url = os.environ.get("NEWSLETTER_API_URL", "http://localhost:8000")
    api_key = os.environ.get("NEWSLETTER_API_KEY")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(
            f"{api_url}/newsletter/admin/send-monthly",
            headers=headers,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Monthly newsletters sent successfully: {result}")
            return result
        else:
            error_msg = f"❌ Failed to send monthly newsletters: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Error sending monthly newsletters: {str(e)}"
        print(error_msg)
        raise


@app.function(
    image=image,
    secrets=[newsletter_api_url, newsletter_api_key]
)
def send_newsletters_manually(frequency: str = "daily"):
    """Manual trigger for testing - can be called with 'daily', 'weekly', or 'monthly'"""
    
    api_url = os.environ.get("NEWSLETTER_API_URL", "http://localhost:8000")
    api_key = os.environ.get("NEWSLETTER_API_KEY")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    endpoint_map = {
        "daily": "send-daily",
        "weekly": "send-weekly", 
        "monthly": "send-monthly"
    }
    
    if frequency not in endpoint_map:
        raise ValueError(f"Invalid frequency: {frequency}. Must be 'daily', 'weekly', or 'monthly'")
    
    try:
        response = requests.post(
            f"{api_url}/newsletter/admin/{endpoint_map[frequency]}",
            headers=headers,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {frequency.title()} newsletters sent successfully: {result}")
            return result
        else:
            error_msg = f"❌ Failed to send {frequency} newsletters: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Error sending {frequency} newsletters: {str(e)}"
        print(error_msg)
        raise


# Health check function
@app.function(image=image)
def health_check():
    """Health check function"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "howyoubeen-newsletter-cron"
    }


if __name__ == "__main__":
    # For local testing
    print("Testing newsletter cron functions...")
    
    # You can test manually by uncommenting one of these:
    # send_daily_newsletters.remote()
    # send_weekly_newsletters.remote() 
    # send_monthly_newsletters.remote()
    # send_newsletters_manually.remote("daily")
    
    print("Newsletter cron app defined successfully!")
    print("\nTo deploy:")
    print("modal deploy modal_newsletter_cron.py")
    print("\nTo test manually:")
    print("modal run modal_newsletter_cron.py::send_newsletters_manually --frequency daily")
