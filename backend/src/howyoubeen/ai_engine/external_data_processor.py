"""
External Data Processor with LLM Integration

Processes data from external sources (GitHub, websites, Google Photos, LinkedIn)
and converts them into LifeEvent and LifeFact objects using LiteLLM.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from litellm import completion
from pydantic import BaseModel

from ..data_models.models import LifeEvent, LifeFact, VisibilityCategory
from ..data_models.enums import VisibilityCategoryType
from ..integrations.github_client import GitHubClient, get_github_data
from ..integrations.firecrawl_client import FirecrawlClient, scrape_personal_website

logger = logging.getLogger(__name__)


class ProcessedExternalData(BaseModel):
    """Container for processed external data"""
    platform: str
    username_or_url: str
    life_events: List[LifeEvent]
    life_facts: List[LifeFact]
    processing_summary: Dict[str, Any]
    raw_data: Dict[str, Any]


class ExternalDataProcessor:
    """Processes external data sources using LLM analysis"""

    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """
        Initialize the external data processor
        
        Args:
            openai_api_key: OpenAI API key (optional, will use env var if not provided)
            anthropic_api_key: Anthropic API key (optional, will use env var if not provided)
        """
        # Set API keys from parameters or environment
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        if anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

        self.default_model = "sonnet-4"  # Cost-effective default
        self.complex_model = "sonnet-4"  # For complex analysis

    def _choose_model(self, complexity: str = "medium") -> str:
        """Choose appropriate model based on task complexity"""
        model_mapping = {
            "simple": "claude-sonnet-4-20250514",
            "medium": "claude-sonnet-4-20250514",
            "complex": "claude-sonnet-4-20250514",
            "analysis": "claude-sonnet-4-20250514",
        }
        return model_mapping.get(complexity, self.default_model)

    async def _llm_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> str:
        """Make LLM completion request with error handling"""
        print(f"[DEBUG] LLM Completion Request:")
        print(f"[DEBUG] Model: {model or self.default_model}")
        print(f"[DEBUG] Messages: {messages}")

        try:
            # Check if we have API keys configured
            if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
                logger.warning("No LLM API keys configured, using mock response")
                print(f"[DEBUG] No API keys configured, using mock response")
                mock_response = self._get_mock_response(messages)
                print(f"[DEBUG] Mock response: {mock_response}")
                return mock_response

            response = completion(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            llm_response = response.choices[0].message.content
            print(f"[DEBUG] LLM Response: {llm_response}")
            return llm_response

        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            print(f"[DEBUG] LLM completion error: {e}")
            logger.info("Falling back to mock response")
            mock_response = self._get_mock_response(messages)
            print(f"[DEBUG] Fallback mock response: {mock_response}")
            return mock_response

    def _extract_json_from_response(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract JSON array from LLM response that may contain explanatory text
        
        Handles cases where LLM returns:
        - Pure JSON: [{"summary": "...", "start_date": "..."}]
        - JSON with markdown: ```json\n[...]\n```
        - JSON with explanation: "Looking through the content...\n```json\n[...]\n```"
        - Empty response or no JSON found
        """
        if not response or not response.strip():
            return []
            
        try:
            # First try parsing the whole response as JSON
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
            
        # Look for JSON blocks marked with ```json or ```
        import re
        
        # Try to find JSON block with markdown markers
        json_blocks = re.findall(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL | re.IGNORECASE)
        if json_blocks:
            for block in json_blocks:
                try:
                    return json.loads(block.strip())
                except json.JSONDecodeError:
                    continue
        
        # Try to find JSON array patterns without markers
        json_patterns = re.findall(r'(\[.*?\])', response, re.DOTALL)
        if json_patterns:
            for pattern in json_patterns:
                try:
                    parsed = json.loads(pattern.strip())
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        # If we find "no dates" or similar indicators, return empty array
        no_dates_indicators = [
            "no specific dates",
            "no explicit dates",
            "cannot extract",
            "no dated events",
            "empty array",
            "no clear dates"
        ]
        
        for indicator in no_dates_indicators:
            if indicator in response.lower():
                print(f"[DEBUG] Found 'no dates' indicator: {indicator}")
                return []
        
        print(f"[DEBUG] Could not extract valid JSON from response: {response[:200]}...")
        return None

    def _get_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock response for testing without API keys"""
        if "life facts" in messages[-1]["content"].lower() or "life fact" in messages[-1]["content"].lower():
            # Mock response for life facts
            return '''[
              {
                "summary": "Experienced software developer with expertise in multiple programming languages",
                "category": "professional"
              },
              {
                "summary": "Active open source contributor with numerous public repositories",
                "category": "skills"
              }
            ]'''
        elif "github" in messages[-1]["content"].lower():
            # Mock response for GitHub life events - only return if there are clear date-specific events
            if "extract" in messages[-1]["content"].lower() and "do not" in messages[-1]["content"].lower():
                # For extraction-based prompts, often return empty array since most GitHub data lacks specific dates
                return '[]'
            else:
                return '''[
                  {
                    "summary": "Created major open source project repository",
                    "start_date": "2024-07-15"
                  }
                ]'''
        else:
            # Mock response for website content - extraction-based
            if "extract" in messages[-1]["content"].lower() and ("no specific dates" in messages[-1]["content"].lower() or "only return events" in messages[-1]["content"].lower()):
                # For extraction-based prompts, often return empty array since most websites lack specific dates
                return '[]'
            else:
                return '''[
                  {
                    "summary": "Website launched",
                    "start_date": "2024-01-15"
                  }
                ]'''

    async def process_github_data(
        self, 
        username: str, 
        visibility_config: List[VisibilityCategory],
        github_token: Optional[str] = None
    ) -> ProcessedExternalData:
        """
        Process GitHub data and convert to LifeEvent/LifeFact objects
        
        Args:
            username: GitHub username
            visibility_config: User's visibility settings
            github_token: Optional GitHub personal access token
            
        Returns:
            ProcessedExternalData with generated entries and facts
        """
        logger.info(f"Processing GitHub data for user: {username}")
        print(f"[DEBUG] Starting GitHub data processing for user: {username}")

        # Collect raw GitHub data
        try:
            print(f"[DEBUG] Collecting raw GitHub data...")
            raw_data = await get_github_data(username, github_token)
            print(f"[DEBUG] Raw GitHub data collected successfully. Repositories: {raw_data['summary']['total_repositories']}")
        except Exception as e:
            logger.error(f"Failed to collect GitHub data for {username}: {e}")
            print(f"[DEBUG] ERROR collecting GitHub data: {e}")
            raise

        # Generate life events using LLM
        print(f"[DEBUG] Generating life events...")
        life_events = await self._generate_github_life_events(raw_data, visibility_config)
        print(f"[DEBUG] Generated {len(life_events)} life events")

        # Generate life facts using LLM
        print(f"[DEBUG] Generating life facts...")
        life_facts = await self._generate_github_life_facts(raw_data, visibility_config)
        print(f"[DEBUG] Generated {len(life_facts)} life facts")

        processing_summary = {
            "total_repositories": raw_data["summary"]["total_repositories"],
            "primary_languages": raw_data["summary"]["primary_languages"],
            "activity_level": raw_data["summary"]["activity_level"],
            "events_generated": len(life_events),
            "facts_generated": len(life_facts)
        }

        print(f"[DEBUG] Processing summary: {processing_summary}")

        processed_data = ProcessedExternalData(
            platform="github",
            username_or_url=username,
            life_events=life_events,
            life_facts=life_facts,
            processing_summary=processing_summary,
            raw_data=raw_data
        )

        print(f"[DEBUG] Created ProcessedExternalData object successfully")
        return processed_data

    async def _generate_github_life_events(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeEvent]:
        """Extract specific life events from GitHub data using LLM"""

        # Prepare context for LLM - focus on date-specific activities
        profile = github_data["profile"]
        repositories = github_data["repositories"][:10]  # Latest 10 repos
        commit_activity = github_data["commit_activity"]

        context = f"""
User Profile: {profile["name"]} (@{profile["login"]})
Account created: {profile["created_at"]}
Bio: {profile.get("bio", "No bio provided")}

Recent Repository Activity (with dates):
{json.dumps([{"name": repo["name"], "description": repo["description"], "language": repo["language"], "created_at": repo["created_at"], "updated_at": repo["updated_at"], "pushed_at": repo["pushed_at"]} for repo in repositories[:5]], indent=2)}

Recent Commits (last 30 days): {commit_activity["commits_last_30_days"]}
Recent commit messages: {commit_activity["recent_commit_messages"][:3]}
"""

        prompt = """
Extract ONLY specific, date-specific life events from this GitHub data. Do NOT create or invent events. Only return events if there is clear evidence of:

1. Repository creation dates for significant projects
2. Major releases or milestones with dates
3. Account creation if it represents a career milestone
4. Clear project launches or completions

Each event must have a specific date and represent a meaningful milestone. If there are no clear date-specific events, return an empty array.

Return the response as a JSON array with this format:
[
  {
    "summary": "Brief description of what actually happened (extracted from data)",
    "start_date": "YYYY-MM-DD"
  }
]

IMPORTANT: Only extract events that actually happened on specific dates. Do not generate or infer events.
"""

        messages = [
            {"role": "system", "content": "You extract specific life events from GitHub data. Only return events with clear dates - do not invent or generate events."},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ]

        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))
            print(f"[DEBUG] GitHub life events raw response: '{response}'")

            # Extract JSON from response - handle cases where LLM adds explanatory text
            json_data = self._extract_json_from_response(response)
            if json_data is None:
                print(f"[DEBUG] No valid JSON found in GitHub response, returning empty list")
                return []
                
            print(f"[DEBUG] Parsed GitHub life events: {json_data}")

            # Handle empty arrays gracefully
            if not json_data or len(json_data) == 0:
                print(f"[DEBUG] LLM returned empty array, no date-specific GitHub events found")
                return []

            # Convert to LifeEvent objects
            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )

            life_events = []
            for entry_data in json_data:
                try:
                    if not isinstance(entry_data, dict) or "start_date" not in entry_data or "summary" not in entry_data:
                        print(f"[DEBUG] Skipping invalid GitHub entry data: {entry_data}")
                        continue
                        
                    event = LifeEvent(
                        visibility=default_visibility,
                        start_date=datetime.fromisoformat(entry_data["start_date"]),
                        summary=entry_data["summary"],
                    )
                    life_events.append(event)
                    print(f"[DEBUG] Created GitHub life event: {event.summary}")
                except (KeyError, ValueError, TypeError) as e:
                    print(f"[DEBUG] Skipping invalid GitHub life event data: {entry_data}, error: {e}")
                    continue

            print(f"[DEBUG] Total GitHub life events extracted: {len(life_events)}")
            return life_events

        except Exception as e:
            logger.error(f"Failed to generate GitHub life events: {e}")
            print(f"[DEBUG] General error in GitHub life events extraction: {e}")
            # Return empty list instead of raising for GitHub extraction failures
            print(f"[DEBUG] Returning empty list due to GitHub extraction failure")
            return []

    async def _generate_github_life_facts(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeFact]:
        """Generate life facts from GitHub data using LLM"""

        profile = github_data["profile"]
        summary = github_data["summary"]
        languages = list(github_data["commit_activity"]["languages_used"].keys())

        context = f"""
GitHub Profile Analysis:
- Account created: {profile["created_at"]}
- Total repositories: {summary["total_repositories"]} 
- Programming languages: {languages[:8]}
- Activity level: {summary["activity_level"]}
- Total stars received: {summary["total_stars_received"]}
- Location: {profile.get("location", "Not specified")}
- Company: {profile.get("company", "Not specified")}
- Bio: {profile.get("bio", "No bio")}
"""

        prompt = """
Based on this GitHub profile data, generate 3-4 life facts that capture the person's professional skills, interests, and background. Each fact should:

1. Be relatively timeless (not tied to specific dates)
2. Capture skills, expertise, or professional identity
3. Be written in third person
4. Be specific and meaningful
5. Be 1-2 sentences long

Return the response as a JSON array with this format:
[
  {
    "summary": "Life fact description",
    "category": "professional|skills|interests|background"
  }
]

Focus on demonstrable skills and professional characteristics rather than assumptions.
"""

        messages = [
            {"role": "system", "content": "You are creating professional life facts from GitHub activity. Be accurate and specific."},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ]

        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))

            # Parse JSON response
            facts_data = json.loads(response.strip())

            # Convert to LifeFact objects
            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )

            life_facts = []
            for fact_data in facts_data:
                fact = LifeFact(
                    visibility=default_visibility,
                    summary=fact_data["summary"],
                    category=fact_data["category"]
                )
                life_facts.append(fact)

            return life_facts

        except Exception as e:
            logger.error(f"Failed to generate GitHub life facts: {e}")
            # Return fallback facts
            return self._create_fallback_github_facts(github_data, visibility_config)

    async def process_website_data(
        self, 
        url: str, 
        visibility_config: List[VisibilityCategory],
        firecrawl_api_key: str
    ) -> ProcessedExternalData:
        """
        Process website data and convert to LifeEvent/LifeFact objects
        
        Args:
            url: Website URL to scrape
            visibility_config: User's visibility settings
            firecrawl_api_key: Firecrawl API key
            
        Returns:
            ProcessedExternalData with generated entries and facts
        """
        logger.info(f"Processing website data for: {url}")

        # Collect raw website data
        try:
            raw_data = await scrape_personal_website(url, firecrawl_api_key)
        except Exception as e:
            logger.error(f"Failed to scrape website {url}: {e}")
            # For debugging, create mock data instead of failing completely
            if "ssl" in str(e).lower() or "tls" in str(e).lower() or "500" in str(e):
                logger.info(f"Creating mock data for {url} due to scraping error")
                raw_data = {
                    "platform": "website",
                    "url": url,
                    "collected_at": datetime.now().isoformat(),
                    "page_result": {
                        "url": url,
                        "markdown": f"# Mock Content from {url}\n\nThis is mock content generated because the website could not be scraped due to SSL/server issues.",
                        "metadata": {"title": f"Mock Title for {url}"}
                    },
                    "summary": {
                        "total_pages": 1,
                        "main_content": f"Mock content from {url}",
                        "site_structure": [url]
                    }
                }
            else:
                raise

        # Generate life events and life facts
        life_events = await self._generate_website_life_events(raw_data, visibility_config)
        life_facts = await self._generate_website_life_facts(raw_data, visibility_config)

        processing_summary = {
            "pages_scraped": raw_data["summary"]["total_pages"],
            "content_length": len(raw_data["summary"]["main_content"]),
            "events_generated": len(life_events),
            "facts_generated": len(life_facts)
        }

        return ProcessedExternalData(
            platform="website",
            username_or_url=url,
            life_events=life_events,
            life_facts=life_facts,
            processing_summary=processing_summary,
            raw_data=raw_data
        )

    async def _generate_website_life_events(
        self, 
        website_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeEvent]:
        """Extract specific life events from website content using LLM"""

        main_content = website_data["summary"]["main_content"][:3000]  # Limit content size

        print(f"[DEBUG] Extracting website life events from content...")
        print(f"[DEBUG] Content preview: {main_content[:200]}...")

        prompt = f"""
Extract ONLY specific, date-specific life events from this personal website content. Do NOT create or invent events. Only return events if you can find:

1. Specific dates mentioned for events, achievements, or milestones
2. Publication dates for articles, projects, or work
3. Employment start/end dates
4. Education graduation dates
5. Award or recognition dates
6. Project launch or completion dates

Website Content:
{main_content}

IMPORTANT: Only extract events that have explicit dates mentioned in the content. If no specific dates are found, return an empty array.

Return as JSON array:
[
  {{
    "summary": "Brief description of what actually happened (extracted from content)",
    "start_date": "YYYY-MM-DD"
  }}
]
"""

        messages = [
            {"role": "system", "content": "You extract specific dated events from website content. Only return events with explicit dates - do not invent dates or events."},
            {"role": "user", "content": prompt}
        ]

        try:
            print(f"[DEBUG] Sending website life events extraction request to LLM...")
            response = await self._llm_completion(messages, model=self._choose_model("medium"))

            print(f"[DEBUG] Website life events raw response: '{response}'")

            if not response or not response.strip():
                print(f"[DEBUG] Empty response, returning empty list")
                return []
                
            # Extract JSON from response - handle cases where LLM adds explanatory text
            json_data = self._extract_json_from_response(response)
            if json_data is None:
                print(f"[DEBUG] No valid JSON found in response, returning empty list")
                return []
                
            print(f"[DEBUG] Parsed website life events: {json_data}")

            # Handle empty arrays gracefully
            if not json_data or len(json_data) == 0:
                print(f"[DEBUG] LLM returned empty array, no date-specific events found")
                return []

            entries_data = json_data

            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )

            life_events = []
            for entry_data in entries_data:
                try:
                    if not isinstance(entry_data, dict) or "start_date" not in entry_data or "summary" not in entry_data:
                        print(f"[DEBUG] Skipping invalid entry data: {entry_data}")
                        continue
                        
                    event = LifeEvent(
                        visibility=default_visibility,
                        start_date=datetime.fromisoformat(entry_data["start_date"]),
                        summary=entry_data["summary"]
                    )
                    life_events.append(event)
                    print(f"[DEBUG] Created website life event: {event.summary}")
                except (KeyError, ValueError, TypeError) as e:
                    print(f"[DEBUG] Skipping invalid life event data: {entry_data}, error: {e}")
                    continue

            print(f"[DEBUG] Total website life events extracted: {len(life_events)}")
            return life_events

        except Exception as e:
            print(f"[DEBUG] General error in website life events extraction: {e}")
            logger.error(f"Failed to extract website life events: {e}")
            # Return empty list instead of raising for website extraction failures
            print(f"[DEBUG] Returning empty list due to extraction failure")
            return []

    async def _generate_website_life_facts(
        self, 
        website_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeFact]:
        """Generate life facts from website content using LLM"""

        print(f"[DEBUG] Generating website life facts...")
        print(f"[DEBUG] Website data keys: {list(website_data.keys())}")

        main_content = website_data["summary"]["main_content"][:3000]  # Limit content size
        print(f"[DEBUG] Main content length: {len(main_content)}")
        print(f"[DEBUG] Main content preview: {main_content[:200]}...")

        prompt = f"""
Based on this personal website content, generate 2-3 life facts about the person's background, skills, interests, or professional identity.

Website Content:
{main_content}

Generate life facts that:
1. Capture lasting characteristics, skills, or background
2. Are written in third person
3. Are specific and meaningful
4. Are 1-2 sentences long
5. Focus on demonstrable qualities

Return as JSON array:
[
  {{
    "summary": "Life fact description", 
    "category": "professional|skills|interests|background"
  }}
]
"""

        messages = [
            {"role": "system", "content": "You create accurate life facts from personal website content."},
            {"role": "user", "content": prompt}
        ]

        print(f"[DEBUG] Prompt being sent to LLM:")
        print(f"[DEBUG] System: {messages[0]['content']}")
        print(f"[DEBUG] User: {messages[1]['content'][:500]}...")

        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))
            print(f"[DEBUG] Raw LLM response for website life facts: '{response}'")
            print(f"[DEBUG] Response length: {len(response)}")
            print(f"[DEBUG] Response stripped: '{response.strip()}'")

            if not response or not response.strip():
                print(f"[DEBUG] Empty response from LLM, returning empty list")
                return []

            facts_data = json.loads(response.strip())
            print(f"[DEBUG] Parsed JSON data: {facts_data}")

            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )

            life_facts = []
            for fact_data in facts_data:
                fact = LifeFact(
                    visibility=default_visibility,
                    summary=fact_data["summary"],
                    category=fact_data["category"]
                )
                life_facts.append(fact)
                print(f"[DEBUG] Created life fact: {fact.summary}")

            print(f"[DEBUG] Total website life facts generated: {len(life_facts)}")
            return life_facts

        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON decode error: {e}")
            print(f"[DEBUG] Problematic response: '{response}'")
            logger.error(f"Failed to parse JSON response for website life facts: {e}")
            return []
        except Exception as e:
            print(f"[DEBUG] General error in website life facts generation: {e}")
            logger.error(f"Failed to generate website life facts: {e}")
            return []

    # Fallback methods for when LLM processing fails
    def _create_fallback_github_entries(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeEvent]:
        """Create fallback diary entries when LLM processing fails"""
        default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
            type=VisibilityCategoryType.GOOD_FRIENDS,
            name="Friends"
        )

        entries = []
        activity = github_data.get("commit_activity", {})

        if activity.get("commits_last_30_days", 0) > 0:
            entries.append(LifeEvent(
                visibility=default_visibility,
                start_date=datetime.now() - timedelta(days=15),
                summary=f"Been actively coding lately with {activity['commits_last_30_days']} commits in the past month. Working on some interesting projects!"
            ))

        languages = list(activity.get("languages_used", {}).keys())[:3]
        if languages:
            entries.append(LifeEvent(
                visibility=default_visibility,
                start_date=datetime.now() - timedelta(days=30),
                summary=f"Expanding my skills in {', '.join(languages)} through various coding projects."
            ))

        return entries

    def _create_fallback_github_facts(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeFact]:
        """Create fallback life facts when LLM processing fails"""
        default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
            type=VisibilityCategoryType.GOOD_FRIENDS,
            name="Friends"
        )

        facts = []
        profile = github_data.get("profile", {})
        summary = github_data.get("summary", {})

        # Programming languages fact
        languages = list(github_data.get("commit_activity", {}).get("languages_used", {}).keys())[:5]
        if languages:
            facts.append(LifeFact(
                visibility=default_visibility,
                summary=f"Experienced in programming languages including {', '.join(languages)}",
                category="skills"
            ))

        # Repository count fact
        if summary.get("total_repositories", 0) > 0:
            facts.append(LifeFact(
                visibility=default_visibility,
                summary=f"Maintains {summary['total_repositories']} public repositories on GitHub",
                category="professional"
            ))

        # Location/company if available
        if profile.get("location"):
            facts.append(LifeFact(
                visibility=default_visibility,
                summary=f"Based in {profile['location']}",
                category="background"
            ))

        return facts
