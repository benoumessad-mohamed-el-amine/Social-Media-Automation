import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.database.mongodb_handler import db_handler
from utils.encryption import encryption_handler

load_dotenv()

GRAPH_API_VERSION = "v24.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


async def get_valid_token(account_id: str) -> str:
    """
    Récupère un token valide pour le compte Instagram.
    Rafraîchit automatiquement le token s’il est proche de l’expiration.
    """
    try:
        account = await db_handler.db.social_accounts.find_one({"_id": account_id})
        if not account or "tokens" not in account:
            raise ValueError("Aucun token trouvé pour ce compte Instagram.")

        encrypted_token = account["tokens"]["access_token"]
        access_token = encryption_handler.decrypt_token(encrypted_token)
        expires_at = account["tokens"].get("expires_at")

        if expires_at:
            expires_at = datetime.fromisoformat(expires_at)
            if expires_at <= datetime.utcnow() + timedelta(days=7):
                refreshed = await refresh_long_lived_token(access_token, account_id)
                if refreshed:
                    access_token = refreshed

        return access_token

    except Exception as e:
        print(f"[❌] Erreur get_valid_token : {e}")
        raise


async def refresh_long_lived_token(old_token: str, account_id: str):
    """
    Rafraîchit un token long-lived Instagram.
    """
    try:
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": os.getenv("INSTAGRAM_APP_ID"),
            "client_secret": os.getenv("INSTAGRAM_APP_SECRET"),
            "fb_exchange_token": old_token
        }

        response = requests.get(f"{BASE_URL}/oauth/access_token", params=params)
        data = response.json()

        if "access_token" in data:
            new_token = data["access_token"]
            new_expiration = datetime.utcnow() + timedelta(days=60)

            # Sauvegarde du nouveau token chiffré
            await db_handler.db.social_accounts.update_one(
                {"_id": account_id},
                {"$set": {
                    "tokens.access_token": encryption_handler.encrypt_token(new_token),
                    "tokens.expires_at": new_expiration.isoformat()
                }}
            )
            print("[🔁] Token Instagram rafraîchi avec succès.")
            return new_token
        else:
            print(f"[⚠️] Échec de refresh token : {data}")
            return None

    except Exception as e:
        print(f"[❌] Erreur refresh_long_lived_token : {e}")
        return None


# ------------------------------------------------------
# ✅ POSTER DU CONTENU SUR INSTAGRAM
# ------------------------------------------------------

async def create_media_container(ig_user_id: str, image_url: str, caption: str, access_token: str):
    """
    Étape 1 : Crée un conteneur média (photo ou vidéo).
    """
    url = f"{BASE_URL}/{ig_user_id}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }

    response = requests.post(url, data=params)
    data = response.json()

    if "id" in data:
        print(f"[📸] Conteneur créé : {data['id']}")
        return data["id"]
    else:
        print(f"[⚠️] Erreur création conteneur : {data}")
        return None


async def publish_media(ig_user_id: str, creation_id: str, access_token: str):
    """
    Étape 2 : Publie un média déjà uploadé.
    """
    url = f"{BASE_URL}/{ig_user_id}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    response = requests.post(url, data=params)
    data = response.json()

    if "id" in data:
        print(f"[✅] Publication réussie : {data['id']}")
        return data["id"]
    else:
        print(f"[⚠️] Erreur publication : {data}")
        return None


async def post_photo_instagram(account_id: str, image_url: str, caption: str):
    """
    Fonction complète pour publier une image sur Instagram.
    """
    try:
        access_token = await get_valid_token(account_id)

        # Récupère le user_id Instagram (lié à la page)
        account = await db_handler.db.social_accounts.find_one({"_id": account_id})
        ig_user_id = account.get("social_id")

        if not ig_user_id:
            raise ValueError("Aucun identifiant utilisateur Instagram trouvé.")

        creation_id = await create_media_container(ig_user_id, image_url, caption, access_token)
        if not creation_id:
            raise Exception("Impossible de créer le conteneur média.")

        post_id = await publish_media(ig_user_id, creation_id, access_token)
        return post_id

    except Exception as e:
        print(f"[❌] Erreur post_photo_instagram : {e}")
        return None


# ------------------------------------------------------
# 📊 RÉCUPÉRATION DE POSTS & ANALYTICS
# ------------------------------------------------------

async def get_recent_posts(account_id: str, limit: int = 5):
    """
    Récupère les derniers posts d’un compte Instagram.
    """
    try:
        access_token = await get_valid_token(account_id)
        account = await db_handler.db.social_accounts.find_one({"_id": account_id})
        ig_user_id = account.get("social_id")

        url = f"{BASE_URL}/{ig_user_id}/media"
        params = {
            "fields": "id,caption,media_url,media_type,like_count,comments_count,timestamp",
            "access_token": access_token,
            "limit": limit
        }

        response = requests.get(url, params=params)
        data = response.json()
        posts = data.get("data", [])

        print(f"[📊] {len(posts)} posts récupérés.")
        return posts

    except Exception as e:
        print(f"[❌] Erreur get_recent_posts : {e}")
        return []


async def get_post_insights(media_id: str, account_id: str):
    """
    Récupère les statistiques (likes, commentaires, portée, etc.) pour un post.
    """
    try:
        access_token = await get_valid_token(account_id)

        metrics = "impressions,reach,engagement,likes,comments,saves"
        url = f"{BASE_URL}/{media_id}/insights"
        params = {
            "metric": metrics,
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        data = response.json()

        return data.get("data", [])

    except Exception as e:
        print(f"[❌] Erreur get_post_insights : {e}")
        return []


async def get_account_insights(account_id: str):
    """
    Récupère les statistiques globales du compte (followers, portée, etc.).
    """
    try:
        access_token = await get_valid_token(account_id)
        account = await db_handler.db.social_accounts.find_one({"_id": account_id})
        ig_user_id = account.get("social_id")

        url = f"{BASE_URL}/{ig_user_id}/insights"
        params = {
            "metric": "impressions,reach,profile_views,follower_count",
            "period": "day",
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        data = response.json()
        return data.get("data", [])

    except Exception as e:
        print(f"[❌] Erreur get_account_insights : {e}")
        return []

