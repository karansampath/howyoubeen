"""
External Data Processor with LLM Integration

Processes data from external sources (GitHub, websites, Google Photos, LinkedIn)
and converts them into DiaryEntry and LifeFact objects using LiteLLM.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from litellm import completion
from pydantic import BaseModel

from ..data_models.models import DiaryEntry, LifeFact, VisibilityCategory
from ..data_models.enums import VisibilityCategoryType
from ..integrations.github_client import GitHubClient, get_github_data
from ..integrations.firecrawl_client import FirecrawlClient, scrape_personal_website

logger = logging.getLogger(__name__)


class ProcessedExternalData(BaseModel):
    """Container for processed external data"""
    platform: str
    username_or_url: str
    diary_entries: List[DiaryEntry]
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
            
        self.default_model = "gpt-3.5-turbo"  # Cost-effective default
        self.complex_model = "gpt-4o"         # For complex analysis
    
    def _choose_model(self, complexity: str = "medium") -> str:
        """Choose appropriate model based on task complexity"""
        model_mapping = {
            "simple": "claude-3-haiku",
            "medium": "gpt-3.5-turbo", 
            "complex": "gpt-4o",
            "analysis": "claude-3-5-sonnet-20240620"
        }
        return model_mapping.get(complexity, self.default_model)
    
    async def _llm_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> str:
        """Make LLM completion request with error handling"""
        try:
            response = completion(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise
    
    async def process_github_data(
        self, 
        username: str, 
        visibility_config: List[VisibilityCategory],
        github_token: Optional[str] = None
    ) -> ProcessedExternalData:
        """
        Process GitHub data and convert to DiaryEntry/LifeFact objects
        
        Args:
            username: GitHub username
            visibility_config: User's visibility settings
            github_token: Optional GitHub personal access token
            
        Returns:
            ProcessedExternalData with generated entries and facts
        """
        logger.info(f"Processing GitHub data for user: {username}")
        
        # Collect raw GitHub data
        try:
            raw_data = await get_github_data(username, github_token)
        except Exception as e:
            logger.error(f"Failed to collect GitHub data for {username}: {e}")
            raise
        
        # Generate diary entries using LLM
        diary_entries = await self._generate_github_diary_entries(raw_data, visibility_config)
        
        # Generate life facts using LLM
        life_facts = await self._generate_github_life_facts(raw_data, visibility_config)
        
        processing_summary = {
            "total_repositories": raw_data["summary"]["total_repositories"],
            "primary_languages": raw_data["summary"]["primary_languages"],
            "activity_level": raw_data["summary"]["activity_level"],
            "entries_generated": len(diary_entries),
            "facts_generated": len(life_facts)
        }
        
        return ProcessedExternalData(
            platform="github",
            username_or_url=username,
            diary_entries=diary_entries,
            life_facts=life_facts,
            processing_summary=processing_summary,
            raw_data=raw_data
        )
    
    async def _generate_github_diary_entries(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[DiaryEntry]:
        """Generate diary entries from GitHub data using LLM"""
        
        # Prepare context for LLM
        profile = github_data["profile"]
        repositories = github_data["repositories"][:10]  # Latest 10 repos
        commit_activity = github_data["commit_activity"]
        
        context = f"""
User Profile: {profile["name"]} (@{profile["login"]})
Bio: {profile.get("bio", "No bio provided")}
Location: {profile.get("location", "Not specified")}
Public Repositories: {profile["public_repos"]}
Followers: {profile["followers"]}

Recent Repository Activity:
{json.dumps([{"name": repo["name"], "description": repo["description"], "language": repo["language"], "updated": repo["updated_at"]} for repo in repositories[:5]], indent=2)}

Recent Commits (last 30 days): {commit_activity["commits_last_30_days"]}
Recent commit messages: {commit_activity["recent_commit_messages"][:3]}
Programming Languages: {list(commit_activity["languages_used"].keys())[:5]}
"""

        prompt = """
Based on this GitHub profile data, generate 2-3 recent diary entries that capture the person's recent coding activities and professional development. Each entry should:

1. Focus on recent activities (last 1-3 months)
2. Be written in first person as if the user wrote it
3. Highlight specific projects, achievements, or learning experiences
4. Include relevant technical details but keep it conversational
5. Be 2-3 sentences long

Return the response as a JSON array with this format:
[
  {
    "summary": "Brief diary entry text",
    "start_date": "2024-01-15", 
    "category": "professional|personal|learning"
  }
]

Focus on concrete activities rather than generic statements.
"""

        messages = [
            {"role": "system", "content": "You are helping create personalized diary entries from GitHub activity data. Be specific and authentic."},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ]
        
        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))
            
            # Parse JSON response
            entries_data = json.loads(response.strip())
            
            # Convert to DiaryEntry objects
            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )
            
            diary_entries = []
            for entry_data in entries_data:
                entry = DiaryEntry(
                    visibility=default_visibility,
                    start_date=datetime.fromisoformat(entry_data["start_date"]),
                    summary=entry_data["summary"],
                )
                diary_entries.append(entry)
            
            return diary_entries
            
        except Exception as e:
            logger.error(f"Failed to generate GitHub diary entries: {e}")
            # Return fallback entries
            return self._create_fallback_github_entries(github_data, visibility_config)
    
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
        Process website data and convert to DiaryEntry/LifeFact objects
        
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
            raise
        
        # Generate diary entries and life facts
        diary_entries = await self._generate_website_diary_entries(raw_data, visibility_config)
        life_facts = await self._generate_website_life_facts(raw_data, visibility_config)
        
        processing_summary = {
            "pages_scraped": raw_data["summary"]["total_pages"],
            "content_length": len(raw_data["summary"]["main_content"]),
            "entries_generated": len(diary_entries),
            "facts_generated": len(life_facts)
        }
        
        return ProcessedExternalData(
            platform="website",
            username_or_url=url,
            diary_entries=diary_entries,
            life_facts=life_facts,
            processing_summary=processing_summary,
            raw_data=raw_data
        )
    
    async def _generate_website_diary_entries(
        self, 
        website_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[DiaryEntry]:
        """Generate diary entries from website content using LLM"""
        
        main_content = website_data["summary"]["main_content"][:3000]  # Limit content size
        
        prompt = f"""
Based on this personal website content, generate 1-2 diary entries that capture recent activities, projects, or life updates mentioned on the site.

Website Content:
{main_content}

Generate diary entries that:
1. Focus on recent activities or updates mentioned 
2. Are written in first person
3. Capture personal or professional developments
4. Are 2-3 sentences long
5. Feel authentic and personal

Return as JSON array:
[
  {{
    "summary": "Diary entry text",
    "start_date": "2024-01-15",
    "category": "personal|professional|creative"
  }}
]

If no recent activities are evident, focus on current projects or interests.
"""

        messages = [
            {"role": "system", "content": "You create authentic diary entries from personal website content."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))
            entries_data = json.loads(response.strip())
            
            default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
                type=VisibilityCategoryType.GOOD_FRIENDS,
                name="Friends"
            )
            
            diary_entries = []
            for entry_data in entries_data:
                entry = DiaryEntry(
                    visibility=default_visibility,
                    start_date=datetime.fromisoformat(entry_data["start_date"]),
                    summary=entry_data["summary"]
                )
                diary_entries.append(entry)
            
            return diary_entries
            
        except Exception as e:
            logger.error(f"Failed to generate website diary entries: {e}")
            return []
    
    async def _generate_website_life_facts(
        self, 
        website_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[LifeFact]:
        """Generate life facts from website content using LLM"""
        
        main_content = website_data["summary"]["main_content"][:3000]  # Limit content size
        
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
        
        try:
            response = await self._llm_completion(messages, model=self._choose_model("medium"))
            facts_data = json.loads(response.strip())
            
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
            logger.error(f"Failed to generate website life facts: {e}")
            return []
    
    # Fallback methods for when LLM processing fails
    def _create_fallback_github_entries(
        self, 
        github_data: Dict[str, Any], 
        visibility_config: List[VisibilityCategory]
    ) -> List[DiaryEntry]:
        """Create fallback diary entries when LLM processing fails"""
        default_visibility = visibility_config[0] if visibility_config else VisibilityCategory(
            type=VisibilityCategoryType.GOOD_FRIENDS,
            name="Friends"
        )
        
        entries = []
        activity = github_data.get("commit_activity", {})
        
        if activity.get("commits_last_30_days", 0) > 0:
            entries.append(DiaryEntry(
                visibility=default_visibility,
                start_date=datetime.now() - timedelta(days=15),
                summary=f"Been actively coding lately with {activity['commits_last_30_days']} commits in the past month. Working on some interesting projects!"
            ))
        
        languages = list(activity.get("languages_used", {}).keys())[:3]
        if languages:
            entries.append(DiaryEntry(
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