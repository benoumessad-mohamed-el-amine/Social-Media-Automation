import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.database.mongodb_handler import db_handler
from src.utils.database.model import PlatformType, ScheduledPost, PostStatus

load_dotenv()


async def test():
    await db_handler.connect()

    print("test1 crée l'utilisateur")
    user = await db_handler.get_or_create_user(
        discord_id="123456789",
        discord_username="TestUser#1234"
    )
    print(f"utilisateur créé : {user.discord_username}")

    print("\n test2: crée le compte du réseau social")
    account_id = await db_handler.add_social_account(
        platform=PlatformType.LINKEDIN,
        account_name="Page LinkedIn",
        account_id="linkedin_page_001",
        access_token="mon_token_secret_123",
        refresh_token="refresh_token_456",
        expires_at=datetime.utcnow() + timedelta(days=60),
    )
    print(f"Compte social ajouté avec ID : {account_id}")

    print("\ntest3: récupération des tokens déchiffrés")
    tokens = await db_handler.get_tokens(account_id)
    if tokens:
        print("Tokens récupérés :")
        print(f"Access Token : {tokens['access_token']}")
        print(f"Refresh Token : {tokens['refresh_token']}")
        print(f"Expiration : {tokens['expires_at']}")
    else:
        print("Aucun token trouvé pour ce compte social")

    print("\ntest4: Création d’un post planifié")
    post = ScheduledPost(
        social_account_id=account_id,
        requested_by_discord_id=user.discord_id,
        platform=PlatformType.LINKEDIN,
        content="testpost",
        media_urls=[],
        scheduled_time=datetime.utcnow() + timedelta(seconds=5),
    )
    post_id = await db_handler.create_scheduled_post(post)
    print(f"Post planifié avec ID : {post_id}")

    print("\ntest5: Récupération des posts en attente")
    pending_posts = await db_handler.get_pending_posts(datetime.utcnow() + timedelta(minutes=1))
    print(f"Nombre de posts en attente : {len(pending_posts)}")
    for p in pending_posts:
        print(f"   {p.platform.value} | {p.content[:30]}... | Statut: {p.status}")

    print("\n test6: Mise à jour du statut du post (PUBLISHED)")
    success = await db_handler.update_post_status(post_id, PostStatus.PUBLISHED)
    print("Statut mis à jour !" if success else "Échec de mise à jour")

    print("\nTest 7: Log d’activité...")
    await db_handler.log_activity(
        discord_id="123456789",
        action="post_scheduled",
        social_account_id=account_id,
        platform=PlatformType.LINKEDIN,
        details={"post_id": post_id, "status": "scheduled"}
    )
    print("Log d’activité enregistré")

    print("\nTest 8: Log de commande...")
    await db_handler.log_command(
        discord_id="123456789",
        command_name="!schedule_post",
        command_args={"platform": "linkedin", "time": "10:00"},
        success=True
    )
    print("Log de commande enregistré")

    print("\nTous les tests se sont bien déroulés !")

    await db_handler.close()


if __name__ == "__main__":
    asyncio.run(test())
