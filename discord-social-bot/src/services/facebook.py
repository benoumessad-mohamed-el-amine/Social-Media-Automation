import requests
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FacebookAPI:
    BASE_URL = "https://graph.facebook.com/v18.0/"

    def __init__(self, access_token: str, max_retries: int = 1):
        self.access_token = access_token
        self.max_retries = max_retries

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = urljoin(self.BASE_URL, endpoint)
        if "params" in kwargs:
            kwargs["params"]["access_token"] = self.access_token
        else:
            kwargs["params"] = {"access_token": self.access_token}

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return {"success": True, "data": response.json()}
            except requests.exceptions.RequestException as e:
                logger.error(f"[Attempt {attempt+1}] Facebook API error: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    content = response.content if 'response' in locals() else None
                    return {"success": False, "error": str(e), "response": content}

    # --- Posts ---
    def post_text(self, message: str, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/feed" if page_id else "me/feed"
        return self._make_request("POST", endpoint, data={"message": message})

    def post_image(self, image_url: str, caption: str = "", page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/photos" if page_id else "me/photos"
        return self._make_request("POST", endpoint, data={"url": image_url, "caption": caption})

    # --- Get Posts ---
    def get_posts(self, limit: int = 10, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/posts" if page_id else "me/posts"
        params = {"limit": limit, "fields": "id,message,created_time,attachments"}
        return self._make_request("GET", endpoint, params=params)

    # --- Post Stats ---
    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        params = {
            "fields": "id,likes.summary(true),comments.summary(true),shares"
        }
        return self._make_request("GET", post_id, params=params)

    # --- Comments ---
    def get_comments(self, post_id: str, limit: int = 10) -> Dict[str, Any]:
        endpoint = f"{post_id}/comments"
        params = {"limit": limit, "fields": "id,from,message,created_time"}
        return self._make_request("GET", endpoint, params=params)

    def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        endpoint = f"{comment_id}/comments"
        return self._make_request("POST", endpoint, data={"message": message})

    # --- Comment Moderation ---
    def hide_comment(self, comment_id: str) -> Dict[str, Any]:
        endpoint = comment_id
        return self._make_request("POST", endpoint, data={"is_hidden": "true"})

    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        return self._make_request("DELETE", comment_id)

    # --- Page Info ---
    def get_page_info(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = page_id if page_id else "me"
        params = {"fields": "id,name,followers_count,fan_count"}
        return self._make_request("GET", endpoint, params=params)
