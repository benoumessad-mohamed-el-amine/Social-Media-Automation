import aiohttp
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.database.mongodb_handler import db_handler
from cryptography.fernet import Fernet

load_dotenv()

GRAPH_BASE = "https://graph.facebook.com/v21.0"
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI")

# Clé d’encryption locale
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

class InstagramOAuthHandler:
    def __init__(self):
        pass

    # -------------------- AUTH URL --------------------
    def get_auth_url(self, discord_user_id: str) -> str:
        """
        Retourne l’URL pour autoriser l’utilisateur Instagram
        """
        return (
            f"https://www.facebook.com/v21.0/dialog/oauth?"
            f"client_id={FACEBOOK_APP_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_metadata"
            f"&state={discord_user_id}"
        )

    # -------------------- CALLBACK --------------------
    async def handle_callback(self, code: str, discord_user_id: str):
        """
        Échange le code OAuth contre un access token long-lived
        puis récupère l’IG User ID associé.
        """
        async with aiohttp.ClientSession() as session:
            # --- Étape 1 : échanger le code contre un access token court ---
            token_url = f"{GRAPH_BASE}/oauth/access_token"
            params = {
                "client_id": FACEBOOK_APP_ID,
                "redirect_uri": REDIRECT_URI,
                "client_secret": FACEBOOK_APP_SECRET,
                "code": code
            }
            async with session.get(token_url, params=params) as resp:
                short_token_data = await resp.json()
                if "access_token" not in short_token_data:
                    print("[ERROR] OAuth exchange failed:", short_token_data)
                    return None

            short_token = short_token_data["access_token"]

            # --- Étape 2 : échanger contre un token long-lived ---
            exchange_url = f"{GRAPH_BASE}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": FACEBOOK_APP_ID,
                "client_secret": FACEBOOK_APP_SECRET,
                "fb_exchange_token": short_token
            }
            async with session.get(exchange_url, params=params) as resp:
                long_token_data = await resp.json()
                if "access_token" not in long_token_data:
                    print("[ERROR] Long-lived token exchange failed:", long_token_data)
                    return None

            access_token = long_token_data["access_token"]
            expires_in = long_token_data.get("expires_in", 5184000)  # 60 jours
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # --- Étape 3 : récupérer les pages de l’utilisateur ---
            async with session.get(f"{GRAPH_BASE}/me/accounts", params={"access_token": access_token}) as resp:
                pages_data = await resp.json()
                if "data" not in pages_data or len(pages_data["data"]) == 0:
                    print("[ERROR] No linked Facebook Page found")
                    return None

            page_id = pages_data["data"][0]["id"]

            # --- Étape 4 : récupérer le compte Instagram pro lié à la Page ---
            async with session.get(
                f"{GRAPH_BASE}/{page_id}",
                params={"fields": "instagram_business_account", "access_token": access_token}
            ) as resp:
                page_info = await resp.json()
                ig_user_id = page_info.get("instagram_business_account", {}).get("id")
                if not ig_user_id:
                    print("[ERROR] No Instagram Business Account found.")
                    return None

            # --- Étape 5 : stocker en DB (encrypté) ---
            encrypted_token = fernet.encrypt(access_token.encode()).decode()

            await db_handler.db.social_accounts.update_one(
                {"platform": "INSTAGRAM", "discord_user_id": discord_user_id},
                {"$set": {
                    "account_id": ig_user_id,
                    "access_token": encrypted_token,
                    "token_expiry": expires_at,
                    "is_active": True
                }},
                upsert=True
            )

            print(f"[SUCCESS] Instagram connected for {discord_user_id}")
            return {"ig_user_id": ig_user_id, "expires_at": expires_at}

    # -------------------- TOKEN CHECK --------------------
    async def get_valid_token(self, ig_user_id: str) -> str:
        """
        Vérifie si le token est encore valide, sinon le refresh automatiquement.
        """
        account = await db_handler.db.social_accounts.find_one({"account_id": ig_user_id, "platform": "INSTAGRAM"})
        if not account:
            print("[ERROR] No Instagram account found in DB.")
            return None

        encrypted_token = account.get("access_token")
        if not encrypted_token:
            print("[ERROR] No token found in DB.")
            return None

        access_token = fernet.decrypt(encrypted_token.encode()).decode()
        expires_at = account.get("token_expiry")

        if expires_at and datetime.utcnow() < expires_at:
            # Token encore valide
            return access_token

        # Sinon, refresh du token
        async with aiohttp.ClientSession() as session:
            refresh_url = f"{GRAPH_BASE}/oauth/access_token"
            params = {
                "grant_type": "ig_refresh_token",
                "access_token": access_token
            }
            async with session.get(refresh_url, params=params) as resp:
                refresh_data = await resp.json()
                if "access_token" not in refresh_data:
                    print("[ERROR] Token refresh failed:", refresh_data)
                    return None

            new_token = refresh_data["access_token"]
            new_expiry = datetime.utcnow() + timedelta(days=60)
            encrypted_new_token = fernet.encrypt(new_token.encode()).decode()

            await db_handler.db.social_accounts.update_one(
                {"account_id": ig_user_id},
                {"$set": {
                    "access_token": encrypted_new_token,
                    "token_expiry": new_expiry
                }}
            )

            print(f"[REFRESH] Token refreshed for {ig_user_id}")
            return new_token


instagram_oauth_handler = InstagramOAuthHandler()
