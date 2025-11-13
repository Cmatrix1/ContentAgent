import requests
import logging
from typing import List, Dict, Any, Iterable, Optional, Union
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class GoogleSearchClient:
    """Client for Google Custom Search JSON API with automatic key rotation."""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    CACHE_KEY_PREFIX = "google_api_key_exhausted_"
    CACHE_TIMEOUT = 86400  
    
    def __init__(
        self, 
        api_keys: Optional[Union[str, List[str]]] = None, 
        search_engine_id: Optional[str] = None
    ):
        """
        Initialize the Google Search client with support for multiple API keys.
        
        Args:
            api_keys: Single API key string or list of API keys (defaults to settings.GOOGLE_API_KEYS)
            search_engine_id: Custom Search Engine ID (defaults to settings.GOOGLE_SEARCH_ENGINE_ID)
        """

        if api_keys is None:
            self.api_keys = getattr(settings, 'GOOGLE_API_KEYS', [])
        elif isinstance(api_keys, str):
            self.api_keys = [api_keys]
        else:
            self.api_keys = api_keys
        
        self.api_keys = [key.strip() for key in self.api_keys if key and key.strip()]
        self.search_engine_id = search_engine_id or getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)
        
        if not self.api_keys:
            raise ValueError(
                "At least one Google API key is required. "
                "Set GOOGLE_API_KEYS or GOOGLE_API_KEY in settings."
            )
        if not self.search_engine_id:
            raise ValueError("Search Engine ID is required. Set GOOGLE_SEARCH_ENGINE_ID in settings.")
        
        logger.info(f"Initialized GoogleSearchClient with {len(self.api_keys)} API key(s)")
    
    def _is_key_exhausted(self, api_key: str) -> bool:
        """Check if an API key is marked as exhausted in cache."""
        cache_key = f"{self.CACHE_KEY_PREFIX}{api_key[:10]}" 
        return cache.get(cache_key, False)
    
    def _mark_key_exhausted(self, api_key: str):
        """Mark an API key as exhausted in cache for 24 hours."""
        cache_key = f"{self.CACHE_KEY_PREFIX}{api_key[:10]}"
        cache.set(cache_key, True, self.CACHE_TIMEOUT)
        logger.warning(f"API key {api_key[:10]}... marked as exhausted")
    
    def _is_quota_error(self, response: requests.Response) -> bool:
        """Check if the response indicates a quota exceeded error."""
        if response.status_code == 429: 
            return True
        
        try:
            data = response.json()
            error = data.get('error', {})
            
            if error.get('code') in [403, 429]:
                error_message = error.get('message', '').lower()
                quota_keywords = ['quota', 'limit', 'rate limit', 'usage limit']
                if any(keyword in error_message for keyword in quota_keywords):
                    return True
            
            errors = error.get('errors', [])
            for err in errors:
                reason = err.get('reason', '').lower()
                if reason in ['rateLimitExceeded', 'quotaExceeded', 'dailyLimitExceeded', 'userRateLimitExceeded']:
                    return True
        except (ValueError, AttributeError):
            pass
        
        return False
    
    def _get_available_keys(self) -> List[str]:
        """Get list of API keys that are not exhausted."""
        return [key for key in self.api_keys if not self._is_key_exhausted(key)]
    
    def search(
        self,
        query: str,
        content_type: str = "text",
        num_results: int = 10,
        platforms: Optional[Iterable[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google Custom Search with automatic API key rotation.
        
        Args:
            query: The search query string
            content_type: Type of content to search for ("video" or "text")
            num_results: Number of results to return (max 10 per request)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of search result dictionaries with keys: title, link, snippet, rank, metadata
            
        Raises:
            GoogleSearchError: If all API keys are exhausted or request fails
        """
        available_keys = self._get_available_keys()
        
        if not available_keys:
            raise GoogleSearchError(
                f"All {len(self.api_keys)} API key(s) have exceeded their quota. "
                "Please wait 24 hours or add more API keys."
            )
        
        logger.info(f"Attempting search with {len(available_keys)} available key(s)")
        
        base_params = {
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
        }
        
        if content_type == "video":
            site_filter = "site:youtube.com OR site:instagram.com OR site:linkedin.com"
            base_params["q"] = f"{query} {site_filter}"
        
        if platforms:
            filters = []
            for platform in platforms:
                platform = (platform or "").lower()
                if platform == "youtube":
                    filters.append("site:youtube.com OR site:youtu.be")
                elif platform == "linkedin":
                    filters.append("site:linkedin.com")
                elif platform == "instagram":
                    filters.append("site:instagram.com")
            if filters:
                site_filter = " OR ".join(filters)
                base_params["q"] = f"{query} ({site_filter})"
        elif content_type == "video":
            site_filter = "site:youtube.com OR site:instagram.com OR site:linkedin.com"
            base_params["q"] = f"{query} {site_filter}"

        base_params.update(kwargs)
        
        last_error = None
        
        for idx, api_key in enumerate(available_keys, 1):
            params = {**base_params, "key": api_key}
            
            try:
                logger.debug(f"Trying API key {idx}/{len(available_keys)}")
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                
                if self._is_quota_error(response):
                    logger.warning(f"API key {idx} quota exceeded, trying next key...")
                    self._mark_key_exhausted(api_key)
                    last_error = GoogleSearchError("API quota exceeded")
                    continue

                response.raise_for_status()
                data = response.json()

                logger.info(f"Search successful with API key {idx}")
                results = self._parse_results(data)
                return results
                
            except requests.exceptions.HTTPError as e:
                if e.response and self._is_quota_error(e.response):
                    logger.warning(f"API key {idx} quota exceeded (HTTP error), trying next key...")
                    self._mark_key_exhausted(api_key)
                    last_error = GoogleSearchError(f"API quota exceeded: {str(e)}")
                    continue
                
                raise GoogleSearchError(f"HTTP error: {str(e)}")
                
            except requests.exceptions.RequestException as e:
                last_error = GoogleSearchError(f"Request failed: {str(e)}")
                logger.error(f"Request failed with API key {idx}: {str(e)}")
                continue
                
            except ValueError as e:
                raise GoogleSearchError(f"Failed to parse search response: {str(e)}")
        
        if last_error:
            raise last_error
        else:
            raise GoogleSearchError("Search failed with all available API keys")
    
    def search_multiple_pages(
        self,
        query: str,
        content_type: str = "text",
        total_results: int = 10,
        platforms: Optional[Iterable[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple searches to get more than 10 results.
        
        Args:
            query: The search query string
            content_type: Type of content to search for ("video" or "text")
            total_results: Total number of results to retrieve
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of search result dictionaries
        """
        all_results = []
        start_index = 1
        
        while len(all_results) < total_results:
            remaining = total_results - len(all_results)
            num_to_fetch = min(remaining, 10)
            
            search_kwargs = {**kwargs, "start": start_index}
            
            results = self.search(
                query=query,
                content_type=content_type,
                num_results=num_to_fetch,
                platforms=platforms,
                **search_kwargs,
            )
            
            if not results:
                break 
            
            all_results.extend(results)
            start_index += len(results)
            
            if len(results) < num_to_fetch:
                break
        
        return all_results[:total_results]
    
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the Google API response into a standardized format.
        
        Args:
            data: Raw response data from Google API
            
        Returns:
            List of parsed result dictionaries
        """
        items = data.get("items", [])
        results = []
        
        for idx, item in enumerate(items, start=1):
            result = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "rank": idx,
                "metadata": {
                    "display_link": item.get("displayLink", ""),
                    "formatted_url": item.get("formattedUrl", ""),
                    "html_snippet": item.get("htmlSnippet", ""),
                    "html_title": item.get("htmlTitle", ""),
                    "kind": item.get("kind", ""),
                    "pagemap": item.get("pagemap", {}),
                }
            }
            results.append(result)
        
        return results


class GoogleSearchError(Exception):
    """Exception raised for errors in Google Search operations."""
    pass


def search_google(
        query: str,
        content_type: str = "text",
        num_results: int = 10,
        platforms: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to perform a Google search.
    
    Args:
        query: The search query string
        content_type: Type of content to search for ("video" or "text")
        num_results: Number of results to return
        
    Returns:
        List of search result dictionaries
    """
    client = GoogleSearchClient()
    
    if num_results <= 10:
        return client.search(query, content_type, num_results, platforms=platforms)
    else:
        return client.search_multiple_pages(query, content_type, num_results, platforms=platforms)

