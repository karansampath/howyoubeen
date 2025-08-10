"""
GitHub API Client for collecting user profile and repository data

Provides functionality to authenticate with GitHub and collect:
- User profile information
- Repository data and statistics  
- Commit activity and contribution patterns
- Programming languages used
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GitHubRepository(BaseModel):
    """GitHub repository information"""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stargazers_count: int
    forks_count: int
    size: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    topics: List[str] = []
    is_fork: bool
    is_private: bool


class GitHubProfile(BaseModel):
    """GitHub user profile information"""
    login: str
    name: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    email: Optional[str]
    blog: Optional[str]
    company: Optional[str]
    public_repos: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime


class GitHubCommitActivity(BaseModel):
    """GitHub commit activity summary"""
    total_commits_last_year: int
    commits_last_30_days: int
    most_active_days: List[str]
    languages_used: Dict[str, int]  # language -> line count
    recent_commit_messages: List[str]


class GitHubClient:
    """GitHub API client for data collection"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token (optional for public data)
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = None
        self._rate_limit_remaining = 60  # GitHub rate limit for unauthenticated requests
        self._rate_limit_reset = datetime.now() + timedelta(hours=1)
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HowYouBeen-App/1.0"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
            
        return headers
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API with rate limiting
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: For HTTP errors
            ValueError: For rate limit exceeded
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
            
        # Check rate limit
        if self._rate_limit_remaining <= 1 and datetime.now() < self._rate_limit_reset:
            wait_seconds = (self._rate_limit_reset - datetime.now()).total_seconds()
            logger.warning(f"Rate limit exceeded. Waiting {wait_seconds:.1f} seconds...")
            await asyncio.sleep(wait_seconds)
        
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        
        try:
            response = await self.session.get(url, params=params or {})
            
            # Update rate limit info from headers
            self._rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            reset_timestamp = int(response.headers.get("X-RateLimit-Reset", 0))
            self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"GitHub API request error: {e}")
            raise
    
    async def get_user_profile(self, username: str) -> GitHubProfile:
        """
        Get GitHub user profile information
        
        Args:
            username: GitHub username
            
        Returns:
            GitHubProfile object with user information
        """
        logger.info(f"Fetching GitHub profile for user: {username}")
        
        data = await self._make_request(f"/users/{username}")
        
        return GitHubProfile(
            login=data["login"],
            name=data.get("name"),
            bio=data.get("bio"),
            location=data.get("location"),
            email=data.get("email"),
            blog=data.get("blog"),
            company=data.get("company"),
            public_repos=data["public_repos"],
            followers=data["followers"],
            following=data["following"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        )
    
    async def get_user_repositories(self, username: str, limit: int = 30) -> List[GitHubRepository]:
        """
        Get user's public repositories
        
        Args:
            username: GitHub username
            limit: Maximum number of repositories to fetch
            
        Returns:
            List of GitHubRepository objects
        """
        logger.info(f"Fetching repositories for user: {username}")
        
        repositories = []
        page = 1
        per_page = min(limit, 100)  # GitHub max per page is 100
        
        while len(repositories) < limit:
            params = {
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
            
            data = await self._make_request(f"/users/{username}/repos", params)
            
            if not data:  # No more repositories
                break
                
            for repo_data in data:
                if len(repositories) >= limit:
                    break
                    
                repo = GitHubRepository(
                    name=repo_data["name"],
                    full_name=repo_data["full_name"],
                    description=repo_data.get("description"),
                    language=repo_data.get("language"),
                    stargazers_count=repo_data["stargazers_count"],
                    forks_count=repo_data["forks_count"],
                    size=repo_data["size"],
                    created_at=datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00")),
                    pushed_at=datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")),
                    topics=repo_data.get("topics", []),
                    is_fork=repo_data["fork"],
                    is_private=repo_data["private"]
                )
                repositories.append(repo)
            
            if len(data) < per_page:  # Last page
                break
                
            page += 1
            
        logger.info(f"Retrieved {len(repositories)} repositories for {username}")
        return repositories
    
    async def get_user_languages(self, username: str, repositories: Optional[List[GitHubRepository]] = None) -> Dict[str, int]:
        """
        Get programming languages used by user across repositories
        
        Args:
            username: GitHub username
            repositories: Pre-fetched repositories (optional)
            
        Returns:
            Dictionary mapping language names to usage counts
        """
        if not repositories:
            repositories = await self.get_user_repositories(username, limit=20)
        
        languages = {}
        
        for repo in repositories[:10]:  # Limit to top 10 repos to avoid rate limiting
            if repo.is_fork:  # Skip forked repositories
                continue
                
            try:
                lang_data = await self._make_request(f"/repos/{repo.full_name}/languages")
                for language, bytes_count in lang_data.items():
                    languages[language] = languages.get(language, 0) + bytes_count
                    
                # Small delay to be respectful of rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Could not fetch languages for {repo.full_name}: {e}")
                continue
        
        return languages
    
    async def get_commit_activity(self, username: str) -> GitHubCommitActivity:
        """
        Get user's commit activity and contribution patterns
        
        Args:
            username: GitHub username
            
        Returns:
            GitHubCommitActivity with activity summary
        """
        logger.info(f"Analyzing commit activity for user: {username}")
        
        # Get recent activity from events API
        try:
            events_data = await self._make_request(f"/users/{username}/events/public", {"per_page": 30})
        except Exception as e:
            logger.warning(f"Could not fetch events for {username}: {e}")
            events_data = []
        
        # Analyze push events for commit activity
        commit_count_30_days = 0
        recent_commit_messages = []
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for event in events_data:
            if event["type"] == "PushEvent":
                event_date = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if event_date > thirty_days_ago:
                    commit_count_30_days += len(event.get("payload", {}).get("commits", []))
                    
                    # Extract commit messages
                    for commit in event.get("payload", {}).get("commits", [])[:3]:  # Limit per event
                        if len(recent_commit_messages) < 10:
                            recent_commit_messages.append(commit.get("message", ""))
        
        # Get languages across repositories
        repositories = await self.get_user_repositories(username, limit=10)
        languages_used = await self.get_user_languages(username, repositories)
        
        return GitHubCommitActivity(
            total_commits_last_year=commit_count_30_days * 12,  # Rough estimate
            commits_last_30_days=commit_count_30_days,
            most_active_days=["Monday", "Tuesday", "Wednesday"],  # Placeholder
            languages_used=languages_used,
            recent_commit_messages=recent_commit_messages[:5]  # Top 5 recent messages
        )
    
    async def collect_user_data(self, username: str) -> Dict[str, Any]:
        """
        Collect comprehensive user data from GitHub
        
        Args:
            username: GitHub username
            
        Returns:
            Dictionary with all collected data
        """
        logger.info(f"Starting comprehensive data collection for GitHub user: {username}")
        
        try:
            # Collect all data concurrently where possible
            profile = await self.get_user_profile(username)
            repositories = await self.get_user_repositories(username, limit=20)
            
            # Sequential for rate limiting
            commit_activity = await self.get_commit_activity(username)
            
            # Compile summary statistics
            total_stars = sum(repo.stargazers_count for repo in repositories)
            total_forks = sum(repo.forks_count for repo in repositories)
            languages = list(commit_activity.languages_used.keys())
            
            recent_repos = [repo for repo in repositories 
                          if repo.pushed_at > datetime.now() - timedelta(days=90)]
            
            collected_data = {
                "platform": "github",
                "username": username,
                "collected_at": datetime.now().isoformat(),
                "profile": profile.dict(),
                "repositories": [repo.dict() for repo in repositories],
                "commit_activity": commit_activity.dict(),
                "summary": {
                    "total_repositories": len(repositories),
                    "total_stars_received": total_stars,
                    "total_forks": total_forks,
                    "primary_languages": languages[:5],
                    "recent_active_repos": len(recent_repos),
                    "account_age_years": (datetime.now() - profile.created_at).days / 365.25,
                    "activity_level": "high" if commit_activity.commits_last_30_days > 10 else "moderate" if commit_activity.commits_last_30_days > 0 else "low"
                }
            }
            
            logger.info(f"Successfully collected GitHub data for {username}: {len(repositories)} repos, {len(languages)} languages")
            return collected_data
            
        except Exception as e:
            logger.error(f"Failed to collect GitHub data for {username}: {e}")
            raise


# Convenience functions for easy usage
async def get_github_data(username: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to collect GitHub data for a user
    
    Args:
        username: GitHub username
        token: Optional GitHub personal access token
        
    Returns:
        Collected GitHub data dictionary
    """
    async with GitHubClient(token=token) as client:
        return await client.collect_user_data(username)


async def validate_github_username(username: str, token: Optional[str] = None) -> bool:
    """
    Validate if a GitHub username exists
    
    Args:
        username: GitHub username to validate
        token: Optional GitHub personal access token
        
    Returns:
        True if username exists and is accessible
    """
    try:
        async with GitHubClient(token=token) as client:
            await client.get_user_profile(username)
        return True
    except Exception:
        return False