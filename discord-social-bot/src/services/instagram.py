import aiohttp
import asyncio
from utils.instagram.oauth import instagram_oauth_handler


GRAPH_BASE = "https://graph.facebook.com/v24.0"


class InstagramAPI:
    def __init__(self):
        pass

    # -------------------- HELPERS --------------------
    async def _request(self, method: str, url: str, access_token: str, params=None, json=None):
        """Wrapper pour envoyer les requêtes Graph API Instagram"""
        if params is None:
            params = {}
        params["access_token"] = access_token

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, params=params, json=json) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"[ERROR] Instagram API {method} {url}: {resp.status} — {text}")
                    return None
                try:
                    return await resp.json()
                except Exception as e:
                    print(f"[ERROR] JSON parsing: {e}")
                    return None

    # -------------------- CREATE MEDIA --------------------
    async def post_media(self, ig_user_id: str, caption: str, media_urls: list[str] = None, access_token: str = None):
        """
        Crée et publie un post sur Instagram Business
        (photo unique ou carrousel)
        """
        if not access_token:
            access_token = await instagram_oauth_handler.get_valid_token(ig_user_id)
        if not access_token:
            print("[ERROR] No valid access token.")
            return None

        # --- Cas 1 : une seule image ---
        if media_urls and len(media_urls) == 1:
            media_url = f"{GRAPH_BASE}/{ig_user_id}/media"
            payload = {"caption": caption, "image_url": media_urls[0]}
            create_res = await self._request("POST", media_url, access_token, json=payload)
            if not create_res or "id" not in create_res:
                return None

            creation_id = create_res["id"]

        # --- Cas 2 : plusieurs images (carrousel) ---
        elif media_urls and len(media_urls) > 1:
            child_ids = []
            for url in media_urls:
                child_res = await self._request(
                    "POST",
                    f"{GRAPH_BASE}/{ig_user_id}/media",
                    access_token,
                    json={"image_url": url, "is_carousel_item": True}
                )
                if child_res and "id" in child_res:
                    child_ids.append(child_res["id"])
                await asyncio.sleep(0.5)

            # Crée le post carrousel
            create_res = await self._request(
                "POST",
                f"{GRAPH_BASE}/{ig_user_id}/media",
                access_token,
                json={"caption": caption, "children": child_ids, "media_type": "CAROUSEL"}
            )
            if not create_res or "id" not in create_res:
                return None

            creation_id = create_res["id"]

        else:
            print("[ERROR] No media provided for post.")
            return None

        # --- Étape 2 : publier ---
        publish_res = await self._request(
            "POST",
            f"{GRAPH_BASE}/{ig_user_id}/media_publish",
            access_token,
            json={"creation_id": creation_id}
        )

        if publish_res and "id" in publish_res:
            return publish_res["id"]
        return None

    # -------------------- GET RECENT POSTS --------------------
    async def get_recent_posts(self, ig_user_id: str, limit: int = 5, access_token: str = None):
        """Récupère les derniers posts du compte Instagram."""
        if not access_token:
            access_token = await instagram_oauth_handler.get_valid_token(ig_user_id)
        if not access_token:
            return None

        url = f"{GRAPH_BASE}/{ig_user_id}/media"
        params = {"fields": "id,caption,media_type,media_url,timestamp", "limit": limit}
        res = await self._request("GET", url, access_token, params=params)
        return res.get("data", []) if res else None

    # -------------------- DELETE POST --------------------
    async def delete_post(self, post_id: str, ig_user_id: str, access_token: str = None):
        """Supprime un post Instagram."""
        if not access_token:
            access_token = await instagram_oauth_handler.get_valid_token(ig_user_id)
        if not access_token:
            return False

        url = f"{GRAPH_BASE}/{post_id}"
        res = await self._request("DELETE", url, access_token)
        return res is not None

    # -------------------- GET POST INSIGHTS --------------------
    async def get_post_insights(self, post_id: str, ig_user_id: str, access_token: str = None):
        """Récupère les statistiques d’un post Instagram."""
        if not access_token:
            access_token = await instagram_oauth_handler.get_valid_token(ig_user_id)
        if not access_token:
            return {}

        url = f"{GRAPH_BASE}/{post_id}/insights"
        params = {
            "metric": "engagement,impressions,reach,saved,likes,comments"
        }
        res = await self._request("GET", url, access_token, params=params)
        if not res or "data" not in res:
            return {}

        # Format simple
        insights = {}
        for item in res["data"]:
            insights[item["name"]] = item.get("values", [{}])[0].get("value", 0)
        return insights


instagram_api = InstagramAPI()
