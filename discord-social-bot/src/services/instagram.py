import requests
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class InstagramBusinessAPI:
    BASE_URL = "https://graph.facebook.com/v24.0/"

    def __init__(self, access_token: str, ig_user_id: Optional[str] = None, max_retries: int = 1):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.max_retries = max_retries

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = urljoin(self.BASE_URL, endpoint)
        if 'params' in kwargs:
            kwargs['params']['access_token'] = self.access_token
        else:
            kwargs['params'] = {'access_token': self.access_token}

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return {"success": True, "data": response.json()}
            except requests.exceptions.RequestException as e:
                logger.error(f"[Attempt {attempt+1}] Instagram API error: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    content = response.content if 'response' in locals() else None
                    return {"success": False, "error": str(e), "response": content}

    # --- POSTING ---
    def post_image(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Upload and publish an image on Instagram Business."""
        if not self.ig_user_id:
            return {"success": False, "error": "Missing Instagram user ID."}

        # Step 1: Create media container
        create_endpoint = f"{self.ig_user_id}/media"
        create_data = {"image_url": image_url, "caption": caption}
        container = self._make_request("POST", create_endpoint, data=create_data)

        if not container.get("success"):
            return container

        # Step 2: Publish the media
        publish_endpoint = f"{self.ig_user_id}/media_publish"
        publish_data = {"creation_id": container["data"]["id"]}
        return self._make_request("POST", publish_endpoint, data=publish_data)

    def post_text(self, caption: str) -> Dict[str, Any]:
        """Simulate text post by using placeholder image."""
        placeholder = "https://via.placeholder.com/1080x1080.png?text=" + requests.utils.quote(caption)
        return self.post_image(placeholder, caption)

    # --- GET POSTS ---
    def get_recent_posts(self, limit: int = 5) -> Dict[str, Any]:
        if not self.ig_user_id:
            return {"success": False, "error": "Missing Instagram user ID."}

        endpoint = f"{self.ig_user_id}/media"
        params = {"fields": "id,caption,media_url,timestamp,like_count,comments_count", "limit": limit}
        return self._make_request("GET", endpoint, params=params)

    # --- ANALYTICS ---
    def get_insights(self, media_id: str) -> Dict[str, Any]:
        """Get insights for a specific post."""
        endpoint = f"{media_id}/insights"
        params = {"metric": "impressions,reach,engagement"}
        return self._make_request("GET", endpoint, params=params)

    def get_account_stats(self) -> Dict[str, Any]:
        """Get overall profile stats (followers, media count, username)."""
        if not self.ig_user_id:
            return {"success": False, "error": "Missing Instagram user ID."}
        endpoint = f"{self.ig_user_id}"
        params = {"fields": "username,followers_count,media_count"}
        return self._make_request("GET", endpoint, params=params)
