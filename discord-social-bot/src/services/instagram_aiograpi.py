import asyncio
from aiograpi import Client
from aiograpi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes
from aiograpi.types import Media, User,Story,StoryHashtag,StoryLink,StoryLocation,StoryMedia
from aiograpi.exceptions import (
    PhotoConfigureError,
    PhotoConfigureStoryError,
    PhotoNotUpload,
)
import os
import random
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InstagramAiograpiService:
    def __init__(self):
        self.client = Client()
        self.username = None
        self.is_logged_in = False
    
    # ==================== AUTHENTIFICATION ====================
    
    async def login(self, username: str, password: str, session_file: str = None) -> bool:
        """
        Tente de se connecter à Instagram en utilisant d'abord la session existante,
        puis les identifiants si nécessaire.
        """
        print(f"Connexion à Instagram: {username}")
        
        if not session_file:
            session_file = f"sessions/session_{username}.json"
        
        login_via_session = False
        login_via_pw = False
        
        # Tentative de connexion via session existante
        if os.path.exists(session_file):
            try:
                print("Session existante trouvée, tentative de chargement...")
                session = self.client.load_settings(session_file)
                
                if session:
                    self.client.set_settings(session)
                    await self.client.login(username, password)
                    
                    # Vérification que la session est valide
                    try:
                        await self.client.get_timeline_feed()
                        login_via_session = True
                        print("Connexion réussie via session")
                    except LoginRequired:
                        print("Session invalide, connexion via identifiants nécessaire")
                        
                        old_session = self.client.get_settings()
                        self.client.set_settings({})
                        self.client.set_uuids(old_session["uuids"])
                        
                        await self.client.login(username, password)
                        login_via_pw = True
                        
            except Exception as e:
                print(f"Échec connexion via session: {e}")
                logger.warning(f"Couldn't login using session: {e}")
        
        # Tentative de connexion via username/password si session a échoué
        if not login_via_session and not login_via_pw:
            try:
                print("Nouvelle connexion via identifiants...")
                if await self.client.login(username, password):
                    login_via_pw = True
                    print("Connexion réussie via identifiants")
                    
                    # Sauvegarder la session pour la prochaine fois
                    os.makedirs("sessions", exist_ok=True)
                    self.client.dump_settings(session_file)
                    print(f"Session sauvegardée: {session_file}")
                    
            except ChallengeRequired as e:
                print(f"Challenge requis (vérification): {e}")
                logger.error(f"Challenge required: {e}")
                return False
            except PleaseWaitFewMinutes as e:
                print(f"Rate limit atteint: {e}")
                logger.error(f"Rate limit: {e}")
                return False
            except Exception as e:
                print(f"Erreur lors de la connexion: {e}")
                logger.error(f"Login error: {e}")
                return False
        
        # Vérification finale
        if not login_via_pw and not login_via_session:
            print("Échec de connexion avec session et identifiants")
            raise Exception("Couldn't login user with either password or session")
        
        # Si connexion réussie via password, sauvegarder la session
        if login_via_pw and not login_via_session:
            try:
                os.makedirs("sessions", exist_ok=True)
                self.client.dump_settings(session_file)
                print(f"Session sauvegardée: {session_file}")
            except Exception as e:
                logger.warning(f"Couldn't save session: {e}")
        
        self.username = username
        self.is_logged_in = True
        print("Connexion réussie")
        return True
    
    async def logout(self) -> bool:
        """Déconnexion de Instagram"""
        try:
            await self.client.logout()
            self.is_logged_in = False
            print("Déconnexion réussie")
            return True
        except Exception as e:
            print(f"Erreur déconnexion: {e}")
            return False
    # ==================== PUBLICATION ====================
    
    async def post_photo(self, image_path: str, caption: str) -> Optional[Media]:
        """Publie une photo sur Instagram"""
        if not self.is_logged_in:
            print("Pas connecté")
            return None
        
        try:
            await self._human_delay(2, 4)
            media = await self.client.photo_upload(image_path, caption)
            print(f"Photo publiée: {media.pk}")
            return media
        except Exception as e:
            print(f"Erreur publication: {e}")
            return None
    
    async def post_video(self, video_path: str, caption: str, thumbnail_path: str = None) -> Optional[Media]:
        """Publie une vidéo sur Instagram"""
        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(3, 5)
            media = await self.client.video_upload(video_path, caption, thumbnail=thumbnail_path)
            print(f"Vidéo publiée: {media.pk}")
            return media
        except Exception as e:
            print(f"Erreur: {e}")
            return None
          
    async def post_story_photo(self, image_path: str) -> Optional[Media]:
        """Publie une story photo"""
        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(2, 3)
            story = await self.client.photo_upload_to_story(image_path)
            print(f"Story publiée: {story.pk}")
            return story
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    # ==================== RÉCUPÉRATION D'INFOS ====================
    
    async def get_user_info(self, username: str) -> Optional[User]:
        """Récupère les informations d'un utilisateur"""
        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(1, 2)
            user_id = await self.client.user_id_from_username(username)
            user = await self.client.user_info(user_id)
            return user
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    async def get_user_posts(self, username: str, limit: int = 10) -> Optional[List[Media]]:

        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(1, 3)
            user_id = await self.client.user_id_from_username(username)
            medias = await self.client.user_medias(user_id, amount=limit)
            return medias
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    async def get_post_info(self, media_id: str) -> Optional[Media]:

        if not self.is_logged_in:
            return None
        
        try:
            media = await self.client.media_info(media_id)
            return media
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    async def get_followers(self, username: str, limit: int = 50) -> Optional[Dict]:

        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(2, 4)
            user_id = await self.client.user_id_from_username(username)
            followers = await self.client.user_followers(user_id, amount=limit)
            return followers
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    async def get_following(self, username: str, limit: int = 50) -> Optional[Dict]:

        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(2, 4)
            user_id = await self.client.user_id_from_username(username)
            following = await self.client.user_following(user_id, amount=limit)
            return following
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    # ==================== INTERACTIONS ====================
    
    async def like_post(self, media_id: str) -> bool:
        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(3, 6)
            await self.client.media_like(media_id)
            print(f"Post liké: {media_id}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    async def unlike_post(self, media_id: str) -> bool:
        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(2, 4)
            await self.client.media_unlike(media_id)
            print(f"Post unliké: {media_id}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    async def comment_post(self, media_id: str, text: str) -> bool:
        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(5, 10)
            await self.client.media_comment(media_id, text)
            print(f"Commentaire posté: {text}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    async def follow_user(self, username: str) -> bool:

        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(4, 8)
            user_id = await self.client.user_id_from_username(username)
            await self.client.user_follow(user_id)
            print(f"Follow: @{username}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    async def unfollow_user(self, username: str) -> bool:
        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(3, 6)
            user_id = await self.client.user_id_from_username(username)
            await self.client.user_unfollow(user_id)
            print(f"Unfollow: @{username}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    # ==================== MESSAGES DIRECTS ====================
    
    async def send_dm(self, username: str, text: str) -> bool:

        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(5, 10)
            user_id = await self.client.user_id_from_username(username)
            await self.client.direct_send(text, [user_id])
            print(f"DM envoyé à @{username}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    async def send_dm_photo(self, username: str, image_path: str, text: str = "") -> bool:

        if not self.is_logged_in:
            return False
        
        try:
            await self._human_delay(6, 12)
            user_id = await self.client.user_id_from_username(username)
            await self.client.direct_send_photo(image_path, [user_id], text)
            print(f"Photo envoyée en DM à @{username}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    # ==================== RECHERCHE ====================
    
    async def search_users(self, query: str, limit: int = 10) -> Optional[List[User]]:

        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(2, 4)
            users = await self.client.search_users(query, amount=limit)
            return users
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    async def search_hashtag(self, hashtag: str) -> Optional[Dict]:

        if not self.is_logged_in:
            return None
        
        try:
            await self._human_delay(2, 3)
            info = await self.client.hashtag_info(hashtag)
            return info
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    # ==================== UTILITAIRES ====================
    
    async def _human_delay(self, min_sec: float = 2, max_sec: float = 5):
        """
        Délai aléatoire pour simuler un comportement humain
        
        Args:
            min_sec: Délai minimum en secondes
            max_sec: Délai maximum en secondes
        """
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    def get_media_url(self, media: Media) -> str:
        """
        Extrait l'URL d'un média
        
        Args:
            media: Objet Media
        
        Returns:
            str: URL de l'image/vidéo
        """
        if media.media_type == 1:  # Photo
            return media.thumbnail_url
        elif media.media_type == 2:  # Video
            return media.video_url
        return None
    
    def format_user_stats(self, user: User) -> Dict:
        """
        Formate les stats d'un utilisateur
        
        Args:
            user: Objet User
        
        Returns:
            Dict: Stats formatées
        """
        return {
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.biography,
            "followers": user.follower_count,
            "following": user.following_count,
            "posts": user.media_count,
            "is_verified": user.is_verified,
            "is_private": user.is_private,
            "profile_pic": user.profile_pic_url
        }


# Instance globale
instagram_aiograpi_service = InstagramAiograpiService()