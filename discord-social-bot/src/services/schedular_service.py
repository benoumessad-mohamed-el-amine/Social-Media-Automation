from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, UTC, timedelta
from typing import Optional
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database.mongodb_handler import db_handler
from utils.database.model import PlatformType, PostStatus, ScheduledPost
 #test
class SchedulerService:
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self._db_handler = None
        print("Scheduler initialisé")
    
    def start(self, db_handler_instance=None):
        if not self.is_running:
            # Stocker la référence au db_handler si fournie
            if db_handler_instance:
                self._db_handler = db_handler_instance
            else:
                self._db_handler = db_handler
            
            # Check for pending posts every minute
            #self.scheduler.add_job(
            #    self.process_pending_posts,
            #    CronTrigger(minute="*"),  # Every minute
            #    id="process_pending_posts",
            #    replace_existing=True
            #)
            
            # Optional: Check every 10 seconds (for testing)
            self.scheduler.add_job(
                self.process_pending_posts,
                'interval',
                seconds=10,
                id="process_pending_posts_fast",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            print(" scheduler démarré - vérifie toutes les 10 secondes")
            print("   prochain check:", datetime.now(UTC).strftime('%H:%M:%S'))
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print(" scheduler arrêté")
    
    async def process_pending_posts(self):
        """Process posts that are ready to be published"""
        try:
            # Utiliser l'instance stockée
            handler = self._db_handler if self._db_handler else db_handler
            
            # Vérifier que la connexion est active
            if handler.db is None:
                print("  Connexion MongoDB non disponible, tentative de reconnexion...")
                try:
                    await handler.connect()
                except Exception as conn_error:
                    print(f" Échec de reconnexion: {conn_error}")
                    return
            
            current_time = datetime.now(UTC)
            
            # Get posts scheduled before now
            pending_posts = await handler.get_pending_posts(current_time)
            
            if not pending_posts:
                # Afficher uniquement lors du premier check
                if not hasattr(self, '_first_check_done'):
                    print(f"aucun post en attente (vérifié à {current_time.strftime('%H:%M:%S')})")
                    self._first_check_done = True
                return
            
            # Reset le flag pour afficher à nouveau quand on trouve des posts
            self._first_check_done = False
            
            print("\n" + "="*70)
            print(f" {len(pending_posts)} post(s) en attente de publication")
            print(f" heure actuelle: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print("="*70)
            
            for post in pending_posts:
                await self.publish_post(post, handler)
        
        except Exception as e:
            print(f" erreur dans process_pending_posts: {e}")
            import traceback
            traceback.print_exc()
    
    async def publish_post(self, post: ScheduledPost, handler):
        """Publish a single post (TEST MODE - affichage dans le terminal)"""
        try:
            print(f"\n PUBLICATION EN COURS...")
            print(f"   ID Post      : {post.id}")
            print(f"   Plateforme   : {post.platform.value.upper()}")
            print(f"   Compte social: {post.social_account_id}")
            print(f"   Demandeur    : {post.requested_by_discord_id}")
            print(f"   Prévu pour   : {post.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Tentative n° : {post.attempts + 1}/{post.max_attempts}")
            
            # Route to appropriate platform service
            if post.platform == PlatformType.LINKEDIN:
                platform_post_id = await self._publish_to_linkedin(post)
            elif post.platform == PlatformType.TIKTOK:
                platform_post_id = await self._publish_to_tiktok(post)
            elif post.platform == PlatformType.FACEBOOK:
                platform_post_id = await self._publish_to_facebook(post)
            elif post.platform == PlatformType.INSTAGRAM:
                platform_post_id = await self._publish_to_instagram(post)
            else:
                print(f"    plateforme inconnue: {post.platform}")
                platform_post_id = None
            
            # Update post status
            if platform_post_id:
                await handler.update_post_status(
                    post_id=str(post.id),
                    status=PostStatus.PUBLISHED
                )
                
                # Log activity
                await handler.log_activity(
                    discord_id=post.requested_by_discord_id,
                    action="post_published",
                    social_account_id=post.social_account_id,
                    platform=post.platform,
                    details={
                        "post_id": str(post.id),
                        "platform_post_id": platform_post_id,
                        "scheduled_time": post.scheduled_time.isoformat(),
                        "published_at": datetime.now(UTC).isoformat()
                    }
                )
                
                print(f"   PUBLIÉ avec succès!")
                print(f"    ID Plateforme: {platform_post_id}")
            else:
                # Mark as failed
                await handler.update_post_status(
                    post_id=str(post.id),
                    status=PostStatus.FAILED,
                    error_message="Échec de publication (mode test)"
                )
                print(f"    ÉCHEC de publication")
        
        except Exception as e:
            print(f"    ERREUR: {e}")
            
            # Update with error
            await handler.update_post_status(
                post_id=str(post.id),
                status=PostStatus.FAILED,
                error_message=str(e)
            )
    
    
    async def _publish_to_linkedin(self, post: ScheduledPost) -> Optional[str]:
        """
        Publish to LinkedIn
        
        TODO: Implémenter les vrais services pour chaque réseau et leurs fonctions de post
              On enlève toute cette partie et on la remplace avec les fonctions réelles mor madrihom je vais changer cette partie
        """
        print("\n      📘 SIMULATION LINKEDIN:")
        print(f"         Contenu: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
        if post.media_urls:
            print(f"         Médias: {len(post.media_urls)} fichier(s)")
            for i, url in enumerate(post.media_urls, 1):
                print(f"            {i}. {url}")
        else:
            print("         Type: Texte seulement")
        
        # Simuler un délai de publication
        import asyncio
        await asyncio.sleep(1)
        
        # Retourner un ID fictif
        return f"linkedin_test_{datetime.now(UTC).timestamp()}"
    
    async def _publish_to_tiktok(self, post: ScheduledPost) -> Optional[str]:
        """
        Publish to TikTok
        
        TODO: Implémenter le service TikTok
        """
        print("\n       SIMULATION TIKTOK:")
        print(f"         Caption: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
        if post.media_urls:
            print(f"         Vidéo: {post.media_urls[0]}")
        else:
            print("          Pas de vidéo attachée")
        
        import asyncio
        await asyncio.sleep(1)
        
        return f"tiktok_test_{datetime.now(UTC).timestamp()}"
    
    async def _publish_to_facebook(self, post: ScheduledPost) -> Optional[str]:
        """
        Publish to Facebook
        
        TODO: Implémenter le service Facebook
        """
        print("\n      SIMULATION FACEBOOK:")
        print(f"         Message: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
        if post.media_urls:
            print(f"         Photos: {len(post.media_urls)} fichier(s)")
        
        import asyncio
        await asyncio.sleep(1)
        
        return f"facebook_test_{datetime.now(UTC).timestamp()}"
    
    async def _publish_to_instagram(self, post: ScheduledPost) -> Optional[str]:
        """
        Publish to Instagram
        
        TODO: Implémenter le service Instagram
        """
        print("\n     SIMULATION INSTAGRAM:")
        print(f"         Légende: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
        if post.media_urls:
            print(f"         Photo: {post.media_urls[0]}")
        else:
            print("       Pas d'image attachée")
        
        import asyncio
        await asyncio.sleep(1)
        
        return f"instagram_test_{datetime.now(UTC).timestamp()}"


# Singleton instance
scheduler_service = SchedulerService()