import discord
from discord.ext import commands
import logging
import requests
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
                logger.error(f"[Attempt {attempt+1}] Facebook API error: {e}")
                if attempt < self.max_retries:
                    logger.info("Retrying...")
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

    def get_posts(self, limit: int = 10, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/posts" if page_id else "me/posts"
        params = {"limit": limit, "fields": "id,message,created_time,attachments"}
        return self._make_request("GET", endpoint, params=params)

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        return self._make_request("DELETE", post_id)

    def get_page_info(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = page_id if page_id else "me"
        params = {"fields": "id,name,followers_count,fan_count"}
        return self._make_request("GET", endpoint, params=params)


# -----------------------------
# ✅ Discord Cog Wrapper
# -----------------------------
class FacebookCog(commands.Cog):
    """Discord commands for Facebook operations."""

    def __init__(self, bot):
        self.bot = bot
        self.fb = None  # will hold a FacebookAPI instance

    @commands.command(name="fbinit")
    async def fb_init(self, ctx, token: str):
        """Initialize Facebook access token."""
        self.fb = FacebookAPI(access_token=token)
        await ctx.send("✅ Facebook API initialized with provided token.")

    @commands.command(name="fbpost")
    async def fb_post(self, ctx, *, message: str):
        """Post a message to Facebook."""
        if not self.fb:
            await ctx.send("❌ You must initialize the Facebook API first using `/fbinit <token>`.")
            return

        result = self.fb.post_text(message)
        if result["success"]:
            await ctx.send("✅ Message posted successfully!")
        else:
            await ctx.send(f"⚠️ Failed to post: {result['error']}")

    @commands.command(name="fbinfo")
    async def fb_info(self, ctx):
        """Get page info."""
        if not self.fb:
            await ctx.send("❌ Initialize the Facebook API first.")
            return

        result = self.fb.get_page_info()
        if result["success"]:
            data = result["data"]
            await ctx.send(f"📘 Page Info:\n**Name:** {data.get('name')}\n**Followers:** {data.get('followers_count', 'N/A')}")
        else:
            await ctx.send(f"⚠️ Failed to fetch page info: {result['error']}")


async def setup(bot):
    await bot.add_cog(FacebookCog(bot))
