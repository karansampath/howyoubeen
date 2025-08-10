# LLM Usage Guide with LiteLLM

This document explains how to use LiteLLM in the KeepInTouch backend for AI-powered features.

## What is LiteLLM?

LiteLLM is a Python library that provides a unified interface for working with 100+ Large Language Model providers. It standardizes the API across different providers (OpenAI, Anthropic, Azure, etc.) while maintaining compatibility with the OpenAI SDK format.

## Installation

LiteLLM is already included in our `pyproject.toml`. To install manually:

```bash
poetry add litellm
```

## Key Benefits for KeepInTouch

1. **Multi-provider support**: Switch between OpenAI and Anthropic models seamlessly
2. **Cost optimization**: Use different models based on task complexity
3. **Fallback mechanisms**: Automatic failover between providers
4. **Unified API**: Same code works with different providers
5. **Built-in observability**: Cost tracking and usage monitoring

## Basic Setup

### Environment Variables

Add to your `.env` file:

```bash
# Primary AI providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Azure OpenAI
AZURE_API_KEY=your_azure_key
AZURE_API_BASE=your_azure_endpoint
AZURE_API_VERSION=2023-12-01-preview
```

### Basic Configuration

```python
import os
import litellm
from litellm import completion

# Set up environment variables
os.environ["OPENAI_API_KEY"] = "your-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"

# Optional: Configure logging
litellm.set_verbose = True  # Enable debug logs
```

## Usage Examples

### 1. OpenAI Models

```python
from litellm import completion

# GPT-4 for complex reasoning tasks
response = completion(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an AI assistant helping users stay connected with friends."},
        {"role": "user", "content": "Generate a personalized update about recent activities."}
    ],
    max_tokens=500,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 2. Anthropic Claude Models

```python
# Claude for personality analysis and conversation
response = completion(
    model="claude-3-5-sonnet-20240620",
    messages=[
        {"role": "user", "content": "Analyze this user's personality from their social media posts and suggest how their AI should respond to friends."}
    ],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### 3. Streaming Responses

```python
# For real-time chat experiences
response = completion(
    model="claude-3-5-sonnet-20240620",
    messages=[{"role": "user", "content": "What's new with Sarah?"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 4. Vision Models

```python
# For analyzing uploaded photos
response = completion(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe what's happening in this photo for a friend's update."},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64_image}}
            ]
        }
    ]
)
```

## Recommended Model Usage for KeepInTouch

### 1. User Onboarding & Personality Analysis
- **Model**: `claude-3-5-sonnet-20240620`
- **Why**: Excellent at understanding personality and context
- **Use case**: Initial user interviews, personality profiling

### 2. Friend Tier Responses
- **Model**: `gpt-4o` or `claude-3-haiku`
- **Why**: Fast, cost-effective for generating multiple response variations
- **Use case**: Creating different responses based on friendship levels

### 3. Real-time Chat
- **Model**: `gpt-3.5-turbo` or `claude-3-haiku`
- **Why**: Low latency, cost-effective for conversational responses
- **Use case**: Friend interactions with user's AI

### 4. Content Summarization
- **Model**: `claude-3-haiku`
- **Why**: Fast and accurate at summarizing large amounts of text
- **Use case**: Processing social media posts, creating newsletters

### 5. Image Analysis
- **Model**: `gpt-4-vision-preview`
- **Why**: Best vision capabilities
- **Use case**: Analyzing uploaded photos, understanding visual content

## Implementation Patterns

### 1. Service Class Pattern

```python
class AIService:
    def __init__(self):
        self.personality_model = "claude-3-5-sonnet-20240620"
        self.chat_model = "gpt-3.5-turbo"
        self.vision_model = "gpt-4-vision-preview"
    
    async def analyze_personality(self, user_data: str) -> str:
        response = completion(
            model=self.personality_model,
            messages=[
                {"role": "system", "content": "Analyze personality traits from user data."},
                {"role": "user", "content": user_data}
            ]
        )
        return response.choices[0].message.content
    
    async def generate_friend_response(self, friend_question: str, user_context: str, friendship_level: str) -> str:
        system_prompt = f"Generate a response as this user's AI for a {friendship_level} level friend."
        
        response = completion(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {user_context}\\nQuestion: {friend_question}"}
            ]
        )
        return response.choices[0].message.content
```

### 2. Fallback Pattern

```python
async def generate_response_with_fallback(messages, primary_model="gpt-4o", fallback_model="gpt-3.5-turbo"):
    try:
        response = completion(model=primary_model, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Primary model failed: {e}, trying fallback...")
        response = completion(model=fallback_model, messages=messages)
        return response.choices[0].message.content
```

### 3. Cost Optimization

```python
def choose_model_by_complexity(task_complexity: str) -> str:
    model_mapping = {
        "simple": "claude-3-haiku",      # $0.25/$1.25 per 1M tokens
        "medium": "gpt-3.5-turbo",       # $0.50/$1.50 per 1M tokens  
        "complex": "gpt-4o",             # $5.00/$15.00 per 1M tokens
        "analysis": "claude-3-5-sonnet-20240620"  # $3.00/$15.00 per 1M tokens
    }
    return model_mapping.get(task_complexity, "gpt-3.5-turbo")
```

## Error Handling

```python
import litellm

try:
    response = completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
except litellm.RateLimitError as e:
    print("Rate limit hit, implementing backoff...")
except litellm.AuthenticationError as e:
    print("API key invalid")
except litellm.APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Monitoring and Observability

```python
# Enable cost tracking
import litellm
litellm.success_callback = ["lunary"]  # Or other observability tools

# Custom callback for usage tracking
def track_usage(kwargs, completion_response, start_time, end_time):
    # Log usage to your database
    print(f"Model: {kwargs['model']}")
    print(f"Tokens: {completion_response.usage.total_tokens}")
    print(f"Cost: ${litellm.completion_cost(completion_response)}")

litellm.success_callback.append(track_usage)
```

## Best Practices

1. **Use environment variables** for API keys
2. **Implement fallback mechanisms** between providers
3. **Choose models based on task complexity** to optimize costs
4. **Enable logging** for debugging and monitoring
5. **Set appropriate timeouts** for production use
6. **Cache responses** when possible to reduce API calls
7. **Monitor costs** and usage patterns
8. **Use streaming** for real-time user experiences

## Integration with KeepInTouch Architecture

The AI service should be implemented in `src/keepintouch/ai_engine/` and used across:

- **User onboarding**: Personality analysis and profile creation
- **Friend interactions**: Real-time chat with user's AI
- **Content processing**: Social media integration and summarization  
- **Notifications**: Personalized update generation
- **Analytics**: Understanding user engagement patterns

This unified approach with LiteLLM will make our AI features more robust, cost-effective, and maintainable.