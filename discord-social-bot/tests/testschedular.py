import asyncio
from datetime import datetime, timedelta, UTC, timezone
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.database.mongodb_handler import db_handler
from src.utils.database.model import PlatformType, ScheduledPost, PostStatus
from src.services.schedular_service import scheduler_service


async def create_test_posts():
    """Créer des posts de test"""
    print(" Création de posts de test...")
    
    # D'abord, créer un compte social de test
    social_account_id = await db_handler.add_social_account(
        platform=PlatformType.LINKEDIN,
        account_name="Test Account",
        access_token="test_token_123",
        account_id="test_account_id"
    )
    
    print(f" Compte social créé: {social_account_id}")
    
    # Post 1: À publier dans 30 secondes
    post1 = ScheduledPost(
        social_account_id=social_account_id,
        requested_by_discord_id="123456789",
        platform=PlatformType.LINKEDIN,
        content=" Premier post de test! Ceci devrait être publié dans 30 secondes.",
        media_urls=[],
        scheduled_time=datetime.now(UTC) + timedelta(seconds=30)
    )
    
    post1_id = await db_handler.create_scheduled_post(post1)
    print(f" Post 1 créé: {post1_id}")
    print(f"   Prévu pour: {post1.scheduled_time.strftime('%H:%M:%S')}")
    
    # Post 2: À publier dans 1 minute
    post2 = ScheduledPost(
        social_account_id=social_account_id,
        requested_by_discord_id="123456789",
        platform=PlatformType.TIKTOK,
        content=" Deuxième post de test! Pour TikTok dans 1 minute.",
        media_urls=["https://example.com/video.mp4"],
        scheduled_time=datetime.now(UTC) + timedelta(minutes=1)
    )
    
    post2_id = await db_handler.create_scheduled_post(post2)
    print(f" Post 2 créé: {post2_id}")
    print(f"   Prévu pour: {post2.scheduled_time.strftime('%H:%M:%S')}")
    
    # Post 3: À publier dans 2 minutes
    post3 = ScheduledPost(
        social_account_id=social_account_id,
        requested_by_discord_id="123456789",
        platform=PlatformType.FACEBOOK,
        content="📘 Troisième post de test! Pour Facebook dans 2 minutes.",
        media_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        scheduled_time=datetime.now(UTC) + timedelta(minutes=2)
    )
    
    post3_id = await db_handler.create_scheduled_post(post3)
    print(f" Post 3 créé: {post3_id}")
    print(f"   Prévu pour: {post3.scheduled_time.strftime('%H:%M:%S')}")
    
    # Post 4: Déjà en retard (pour tester immédiatement)
    post4 = ScheduledPost(
        social_account_id=social_account_id,
        requested_by_discord_id="123456789",
        platform=PlatformType.INSTAGRAM,
        content="📸 Quatrième post - EN RETARD! Devrait être publié immédiatement.",
        media_urls=["https://example.com/insta.jpg"],
        scheduled_time=datetime.now(UTC) - timedelta(minutes=1)  # 1 minute dans le passé
    )
    
    post4_id = await db_handler.create_scheduled_post(post4)
    print(f" Post 4 créé: {post4_id}")
    print(f"    EN RETARD - devrait être publié au prochain check!")
    
    return [post1_id, post2_id, post3_id, post4_id]


async def monitor_posts(post_ids: list, duration_minutes: int = 5):
    """Surveiller l'état des posts"""
    print(f"\nSurveillance des posts pendant {duration_minutes} minutes...")
    print("   (Appuyez sur Ctrl+C pour arrêter)")
    
    start_time = datetime.now(UTC)
    last_status = {}
    
    while (datetime.now(UTC) - start_time).total_seconds() < duration_minutes * 60:
        try:
            await asyncio.sleep(10)  # Check toutes les 10 secondes
            
            # Vérifier le statut de chaque post
            for post_id in post_ids:
                post = await db_handler.db.scheduled_posts.find_one({"_id": post_id})
                if post:
                    current_status = post.get('status')
                    
                    # Afficher seulement si le statut a changé
                    if last_status.get(post_id) != current_status:
                        time_str = datetime.now(UTC).strftime('%H:%M:%S')
                        platform = post.get('platform', 'unknown')
                        
                        if current_status == PostStatus.PUBLISHED.value:
                            print(f"   [{time_str}] Post {platform.upper()} publié!")
                        elif current_status == PostStatus.FAILED.value:
                            error = post.get('error_message', 'Erreur inconnue')
                            print(f"   [{time_str}] Post {platform.upper()} échoué: {error}")
                        
                        last_status[post_id] = current_status
        
        except KeyboardInterrupt:
            print("\nSurveillance interrompue")
            break


async def show_final_status(post_ids: list):
    """Afficher le statut final de tous les posts"""
    print("\n" + "="*70)
    print("STATUT FINAL DES POSTS")
    print("="*70)
    
    for i, post_id in enumerate(post_ids, 1):
        post = await db_handler.db.scheduled_posts.find_one({"_id": post_id})
        if post:
            status = post.get('status')
            platform = post.get('platform', 'unknown')
            content = post.get('content', '')[:50]
            scheduled = post.get('scheduled_time')
            published = post.get('published_at')
            
            status_emoji = {
                'scheduled': '⏳',
                'published': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(status, '❓')
            
            print(f"\nPost {i} - {platform.upper()}")
            print(f"  {status_emoji} Statut: {status}")
            print(f"   Contenu: {content}...")
            print(f"   Prévu: {scheduled.strftime('%H:%M:%S') if scheduled else 'N/A'}")
            if published:
                print(f"  Publié: {published.strftime('%H:%M:%S')}")
                delay = (published - scheduled).total_seconds() if scheduled else 0
                print(f"  Délai: {delay:.0f} secondes")


async def main():
    """Fonction principale de test"""
    print("="*70)
    print("TEST DU SCHEDULER SERVICE")
    print("="*70)
    
    try:
        # Connexion à MongoDB POUR LE TEST
        print("\nConnexion à MongoDB (test)...")
        await db_handler.connect()
        
        # Créer des posts de test
        post_ids = await create_test_posts()
        
        print("\n" + "="*70)
        print("HEURE ACTUELLE:", datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC'))
        print("="*70)
        
        # IMPORTANT: Le scheduler utilise la même connexion
        print("\nDémarrage du scheduler...")
        print("   (Utilise la connexion MongoDB existante)")
        scheduler_service.start()
        
        # Monitorer les posts
        await monitor_posts(post_ids, duration_minutes=5)
        
        # Afficher le statut final
        await show_final_status(post_ids)
        
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Arrêter le scheduler
        print("\nArrêt du scheduler...")
        scheduler_service.stop()
        
        # Fermer la connexion MongoDB
        await db_handler.close()
        
        print("\nTest terminé!")
        print("="*70)


if __name__ == "__main__":
    print("\nCe script va:")
    print("   1. Créer 4 posts de test")
    print("   2. Démarrer le scheduler")
    print("   3. Surveiller les publications pendant 5 minutes")
    print("   4. Afficher le résultat final")
    print("\nDémarrage dans 3 secondes...\n")
    
    import time
    time.sleep(3)
    
    asyncio.run(main())