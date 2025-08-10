"""
Firecrawl API Client for web content scraping and crawling

Provides functionality to:
- Scrape individual web pages and convert to markdown
- Crawl entire websites with depth control  
- Extract structured data from web content
- Handle dynamic content and anti-bot mechanisms
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urljoin

import httpx
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)


class FirecrawlScrapedPage(BaseModel):
    """Single scraped page result from Firecrawl"""
    url: str
    markdown: str
    html: Optional[str] = None
    metadata: Dict[str, Any] = {}
    screenshot: Optional[str] = None
    

class FirecrawlCrawlResult(BaseModel):
    """Result from crawling multiple pages"""
    original_url: str
    total_pages: int
    pages: List[FirecrawlScrapedPage]
    crawl_id: Optional[str] = None
    status: str
    

class FirecrawlExtractedData(BaseModel):
    """Structured data extracted from web content"""
    url: str
    extracted_data: Dict[str, Any]
    confidence_score: Optional[float] = None


class FirecrawlClient:
    """Firecrawl API client for web scraping and crawling"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.firecrawl.dev"):
        """
        Initialize Firecrawl client
        
        Args:
            api_key: Firecrawl API key
            base_url: Firecrawl API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=60.0  # Longer timeout for web scraping
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Firecrawl API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to Firecrawl API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request body data
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: For HTTP errors
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
            
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        
        try:
            if method.upper() == "GET":
                response = await self.session.get(url, params=data)
            elif method.upper() == "POST":
                response = await self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Firecrawl API error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Firecrawl API request error: {e}")
            raise
    
    async def scrape_url(
        self,
        url: str,
        formats: List[str] = None,
        include_html: bool = False,
        include_screenshot: bool = False,
        wait_for: Optional[str] = None,
        timeout: int = 30000
    ) -> FirecrawlScrapedPage:
        """
        Scrape a single URL and return the content
        
        Args:
            url: URL to scrape
            formats: Output formats (default: ["markdown"])
            include_html: Whether to include raw HTML
            include_screenshot: Whether to include screenshot
            wait_for: CSS selector to wait for before scraping
            timeout: Timeout in milliseconds
            
        Returns:
            FirecrawlScrapedPage with scraped content
        """
        logger.info(f"Scraping URL: {url}")
        
        if formats is None:
            formats = ["markdown"]
        
        payload = {
            "url": url,
            "formats": formats,
            "includeTags": ["title", "meta", "h1", "h2", "h3", "p", "article"],
            "excludeTags": ["script", "style", "nav", "footer", "header"],
            "onlyMainContent": True,
            "timeout": timeout
        }
        
        if include_html:
            payload["formats"].append("html")
            
        if include_screenshot:
            payload["formats"].append("screenshot")
            
        if wait_for:
            payload["waitFor"] = wait_for
        
        try:
            data = await self._make_request("POST", "/v1/scrape", payload)
            
            result = data.get("data", {})
            
            return FirecrawlScrapedPage(
                url=url,
                markdown=result.get("markdown", ""),
                html=result.get("html") if include_html else None,
                metadata=result.get("metadata", {}),
                screenshot=result.get("screenshot") if include_screenshot else None
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            raise
    
    async def crawl_website(
        self,
        url: str,
        max_depth: int = 2,
        limit: int = 10,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        timeout: int = 30000
    ) -> FirecrawlCrawlResult:
        """
        Crawl an entire website starting from the given URL
        
        Args:
            url: Starting URL for crawling
            max_depth: Maximum depth to crawl
            limit: Maximum number of pages to crawl
            include_paths: URL patterns to include (e.g., ["/blog/*"])
            exclude_paths: URL patterns to exclude
            timeout: Timeout in milliseconds per page
            
        Returns:
            FirecrawlCrawlResult with all crawled pages
        """
        logger.info(f"Starting website crawl: {url} (depth: {max_depth}, limit: {limit})")
        
        payload = {
            "url": url,
            "crawlerOptions": {
                "maxDepth": max_depth,
                "limit": limit,
                "timeout": timeout
            },
            "pageOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
                "includeTags": ["title", "meta", "h1", "h2", "h3", "p", "article"],
                "excludeTags": ["script", "style", "nav", "footer", "header"]
            }
        }
        
        if include_paths:
            payload["crawlerOptions"]["includePaths"] = include_paths
            
        if exclude_paths:
            payload["crawlerOptions"]["excludePaths"] = exclude_paths
        
        try:
            # Start crawl job
            response = await self._make_request("POST", "/v1/crawl", payload)
            crawl_id = response.get("id")
            
            if not crawl_id:
                raise ValueError("No crawl ID returned from Firecrawl API")
            
            # Poll for completion
            max_attempts = 60  # Wait up to 5 minutes
            attempt = 0
            
            while attempt < max_attempts:
                status_data = await self._make_request("GET", f"/v1/crawl/{crawl_id}")
                status = status_data.get("status")
                
                if status == "completed":
                    break
                elif status == "failed":
                    raise RuntimeError(f"Crawl failed: {status_data.get('error', 'Unknown error')}")
                
                # Wait before next check
                await asyncio.sleep(5)
                attempt += 1
            
            if attempt >= max_attempts:
                raise TimeoutError("Crawl timed out after 5 minutes")
            
            # Get final results
            final_data = await self._make_request("GET", f"/v1/crawl/{crawl_id}")
            pages_data = final_data.get("data", [])
            
            pages = []
            for page_data in pages_data:
                page = FirecrawlScrapedPage(
                    url=page_data.get("url", ""),
                    markdown=page_data.get("markdown", ""),
                    metadata=page_data.get("metadata", {})
                )
                pages.append(page)
            
            result = FirecrawlCrawlResult(
                original_url=url,
                total_pages=len(pages),
                pages=pages,
                crawl_id=crawl_id,
                status="completed"
            )
            
            logger.info(f"Crawl completed: {len(pages)} pages scraped from {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to crawl website {url}: {e}")
            raise
    
    async def extract_structured_data(
        self,
        url: str,
        schema: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> FirecrawlExtractedData:
        """
        Extract structured data from a web page using AI
        
        Args:
            url: URL to extract data from
            schema: JSON schema for extracted data structure
            prompt: Optional prompt to guide extraction
            
        Returns:
            FirecrawlExtractedData with structured information
        """
        logger.info(f"Extracting structured data from: {url}")
        
        payload = {
            "url": url,
            "schema": schema,
            "formats": ["extract"]
        }
        
        if prompt:
            payload["prompt"] = prompt
        
        try:
            data = await self._make_request("POST", "/v1/scrape", payload)
            result = data.get("data", {})
            
            return FirecrawlExtractedData(
                url=url,
                extracted_data=result.get("extract", {}),
                confidence_score=result.get("metadata", {}).get("confidence")
            )
            
        except Exception as e:
            logger.error(f"Failed to extract structured data from {url}: {e}")
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    async def scrape_multiple_urls(
        self,
        urls: List[str],
        max_concurrent: int = 3,
        **scrape_options
    ) -> List[FirecrawlScrapedPage]:
        """
        Scrape multiple URLs concurrently with rate limiting
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            **scrape_options: Options passed to scrape_url
            
        Returns:
            List of FirecrawlScrapedPage results
        """
        logger.info(f"Scraping {len(urls)} URLs with max concurrency: {max_concurrent}")
        
        # Filter valid URLs
        valid_urls = [url for url in urls if self._is_valid_url(url)]
        if len(valid_urls) != len(urls):
            logger.warning(f"Filtered out {len(urls) - len(valid_urls)} invalid URLs")
        
        # Semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_limit(url: str) -> Optional[FirecrawlScrapedPage]:
            async with semaphore:
                try:
                    return await self.scrape_url(url, **scrape_options)
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    return None
        
        # Execute all scraping tasks
        tasks = [scrape_with_limit(url) for url in valid_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        successful_results = []
        for result in results:
            if isinstance(result, FirecrawlScrapedPage):
                successful_results.append(result)
        
        logger.info(f"Successfully scraped {len(successful_results)}/{len(valid_urls)} URLs")
        return successful_results


# Convenience functions
async def scrape_personal_website(url: str, api_key: str) -> Dict[str, Any]:
    """
    Scrape a personal website and extract relevant information
    
    Args:
        url: Website URL to scrape
        api_key: Firecrawl API key
        
    Returns:
        Dictionary with scraped content and metadata
    """
    async with FirecrawlClient(api_key) as client:
        # First try to crawl the site for comprehensive data
        try:
            crawl_result = await client.crawl_website(
                url=url,
                max_depth=2,
                limit=10,
                exclude_paths=["/admin/*", "/wp-admin/*", "/login", "/contact"]
            )
            
            return {
                "platform": "website",
                "url": url,
                "collected_at": datetime.now().isoformat(),
                "crawl_result": crawl_result.dict(),
                "summary": {
                    "total_pages": crawl_result.total_pages,
                    "main_content": crawl_result.pages[0].markdown if crawl_result.pages else "",
                    "site_structure": [page.url for page in crawl_result.pages[:5]]
                }
            }
            
        except Exception as e:
            logger.warning(f"Full crawl failed, falling back to single page scrape: {e}")
            
            # Fall back to single page scraping
            page_result = await client.scrape_url(url, include_html=False)
            
            return {
                "platform": "website",
                "url": url,
                "collected_at": datetime.now().isoformat(),
                "page_result": page_result.dict(),
                "summary": {
                    "total_pages": 1,
                    "main_content": page_result.markdown,
                    "site_structure": [url]
                }
            }


async def validate_website_url(url: str, api_key: str) -> bool:
    """
    Validate if a website URL is accessible and scrapable
    
    Args:
        url: Website URL to validate
        api_key: Firecrawl API key
        
    Returns:
        True if URL is valid and accessible
    """
    try:
        async with FirecrawlClient(api_key) as client:
            result = await client.scrape_url(url, timeout=10000)
            return len(result.markdown.strip()) > 100  # Minimum content check
    except Exception:
        return False