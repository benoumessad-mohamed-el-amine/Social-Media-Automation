import asyncio
from datetime import datetime,timezone
from  utils.database.mongodb_handler import db_handler
from utils.database.model import (
    User, SocialMediaAccount, PublishedPost, PlatformType, PlatformTokens,BotCommand
)
from utils.database.encryption import encryption_handler


async def init_db():
    # Connexion à la DB
    await db_handler.connect()

    # -------------------- Users --------------------
    users_data = [
        {"discord_id": "1234567890", "discord_username": "Alice"},
        {"discord_id": "2345678901", "discord_username": "Bob"},
    ]

    users = []
    for u in users_data:
        user = User(discord_id=u["discord_id"], discord_username=u["discord_username"])
        result = await db_handler.db.users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
        user.id = result.inserted_id
        users.append(user)
    print(f"Inserted {len(users)} users")

    # -------------------- Social Accounts --------------------
    accounts_data = [
        {"platform": PlatformType.FACEBOOK, "name": "My Business", "id": "fb_123", "connected": True},
        {"platform": PlatformType.INSTAGRAM, "name": "My Instagram", "id": "ig_123", "connected": True},
        {"platform": PlatformType.LINKEDIN, "name": "My Company", "id": "li_123", "connected": True},
        {"platform": PlatformType.TIKTOK, "name": "My TikTok", "id": "tt_123", "connected": False},
    ]

    accounts = []
    for a in accounts_data:
        account = SocialMediaAccount(
            platform=a["platform"],
            account_name=a["name"],
            account_id=a["id"],
            tokens=PlatformTokens(
                access_token=encryption_handler.encrypt_token(f"{a['id']}_token"),
                refresh_token=None,
                expires_at=None
            ),
            connected_at=datetime.now(timezone.utc),
            is_active=a["connected"]
        )
        result = await db_handler.db.social_accounts.insert_one(account.model_dump(by_alias=True, exclude={"id"}))
        account.id = result.inserted_id
        accounts.append(account)
    print(f"Inserted {len(accounts)} social accounts")

    # -------------------- Published Posts --------------------
    posts_data = [
        {"platform": PlatformType.FACEBOOK, "content": "Hello Facebook!"},
        {"platform": PlatformType.INSTAGRAM, "content": "Hello Instagram!"},
        {"platform": PlatformType.LINKEDIN, "content": "Hello LinkedIn!"},
        {"platform": PlatformType.TIKTOK, "content": "Hello TikTok!"},
    ]

    posts = []
    for p in posts_data:
        # assign a connected account of same platform if exists
        account = next((acc for acc in accounts if acc.platform == p["platform"] and acc.is_active), None)
        if not account:
            continue
        post = PublishedPost(
            social_account_id=str(account.id),
            requested_by_discord_id=users[0].discord_id,
            platform=p["platform"],
            content=p["content"],
            media_urls=[],
            published_at=datetime.now(timezone.utc)
        )
        result = await db_handler.db.published_posts.insert_one(post.model_dump(by_alias=True, exclude={"id"}))
        post.id = result.inserted_id
        posts.append(post)
    print(f"Inserted {len(posts)} published posts")
    
        # -------------------- Bot Commands --------------------
    
    commands_data = [
        ("/accounts", [], "List all connected social media accounts"),
        ("/post", ["platform", "content"], "Post to a specific platform"),
        ("/crosspost", ["content"], "Post to all connected platforms at once"),
        ("/reply", ["platform", "post_id", "comment"], "Reply to a post comment"),
        ("/delete", ["platform", "post_id"], "Delete a post"),
        ("/help", [], "Show this help message"),
        ("/postschedular", ["platform", "content", "date"], "Schedule a post for a future date/time")
    ]

    

    commands = []
    for name, args, description in commands_data:
        cmd = BotCommand(
            name=name,
            description=description,
            args=args,
            category="Socialmediatrackers"  
        )
        result = await db_handler.db.bot_commands.insert_one(cmd.model_dump(by_alias=True, exclude={"id"}))
        cmd.id = result.inserted_id
        commands.append(cmd)


    # -------------------- Close DB --------------------
    await db_handler.close()


if __name__ == "__main__":
    asyncio.run(init_db())