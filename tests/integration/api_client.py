"""
API Client for GovStack Integration Tests
Handles all HTTP requests with logging and error handling
"""

import time
from typing import Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    BASE_URL, API_KEY, ADMIN_API_KEY, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_DELAY
)
from logger import logger


class APIClient:
    """HTTP client for GovStack API with retry logic and logging"""
    
    def __init__(self, use_admin_key: bool = False):
        self.base_url = BASE_URL.rstrip('/')
        self.api_key = ADMIN_API_KEY if use_admin_key else API_KEY
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "X-API-Key": self.api_key
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with logging"""
        url = f"{self.base_url}{endpoint}"
        
        # Add headers
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self._get_headers())
        
        # Set timeout
        if 'timeout' not in kwargs:
            kwargs['timeout'] = REQUEST_TIMEOUT
            
        # Log request
        logger.debug(f"Request: {method} {url}")
        if 'json' in kwargs:
            logger.debug(f"Body: {kwargs['json']}")
            
        try:
            response = self.session.request(method, url, **kwargs)
            logger.api_request(method, endpoint, response.status_code)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """GET request"""
        response = self._make_request("GET", endpoint, params=params, **kwargs)
        return self._handle_response(response)
    
    def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """POST request"""
        response = self._make_request(
            "POST",
            endpoint,
            json=json,
            files=files,
            data=data,
            **kwargs
        )
        return self._handle_response(response)
    
    def put(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        response = self._make_request("PUT", endpoint, json=json, **kwargs)
        return self._handle_response(response)
    
    def patch(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PATCH request"""
        response = self._make_request("PATCH", endpoint, json=json, **kwargs)
        return self._handle_response(response)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        response = self._make_request("DELETE", endpoint, **kwargs)
        return self._handle_response(response)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle response and extract JSON"""
        try:
            data = response.json()
        except ValueError:
            data = {"text": response.text}
            
        logger.debug(f"Response [{response.status_code}]: {data}")
        
        if not response.ok:
            error_msg = data.get('detail', data.get('message', 'Unknown error'))
            logger.error(f"API Error [{response.status_code}]: {error_msg}")
            
        return {
            "status_code": response.status_code,
            "data": data,
            "ok": response.ok
        }
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=REQUEST_TIMEOUT
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def wait_for_indexing_job(
        self,
        job_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Poll indexing job until completion"""
        logger.info(f"⏳ Waiting for indexing job {job_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get(f"/documents/indexing-jobs/{job_id}")
            
            if not result["ok"]:
                logger.error(f"Failed to check indexing job status: {result['data']}")
                return result
            
            job_data = result["data"]
            status = job_data.get("status")
            progress = job_data.get("progress_percent", 0)
            
            logger.debug(f"Job status: {status}, Progress: {progress}%")
            
            if status == "completed":
                logger.info(f"✅ Indexing job completed successfully")
                return result
            elif status == "failed":
                error = job_data.get("error", "Unknown error")
                logger.error(f"❌ Indexing job failed: {error}")
                return result
            
            time.sleep(poll_interval)
        
        logger.warning(f"⏱️  Indexing job timeout after {max_wait}s")
        return {"ok": False, "data": {"error": "Timeout waiting for indexing job"}}
    
    def wait_for_crawl_completion(
        self,
        task_id: str,
        max_wait: int = 600,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """Poll crawl task until completion"""
        logger.info(f"⏳ Waiting for crawl task {task_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get(f"/crawl/{task_id}")
            
            if not result["ok"]:
                logger.error(f"Failed to check crawl status: {result['data']}")
                return result
            
            crawl_data = result["data"]
            status = crawl_data.get("status")
            urls_crawled = crawl_data.get("urls_crawled", 0)
            
            logger.debug(f"Crawl status: {status}, URLs crawled: {urls_crawled}")
            
            if crawl_data.get("finished"):
                logger.info(f"✅ Crawl completed: {urls_crawled} URLs crawled")
                return result
            
            time.sleep(poll_interval)
        
        logger.warning(f"⏱️  Crawl timeout after {max_wait}s")
        return {"ok": False, "data": {"error": "Timeout waiting for crawl completion"}}


# Global client instances
client = APIClient(use_admin_key=False)
admin_client = APIClient(use_admin_key=True)
