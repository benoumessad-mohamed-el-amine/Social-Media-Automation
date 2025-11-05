from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime,timezone
import os
from bson import ObjectId

from .model import (
    User, SocialMediaAccount, ScheduledPost, PublishedPost,
    CommandLog, ActivityLog, BotCommand, ReplyAction,
    PlatformType, PostStatus
)
from .encryption import encryption_handler


class MongoDBHandler:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    # ************************ Connection Mongo **************************
    async def connect(self):
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[os.getenv("MONGODB_DATABASE", "media_tracker")]
        await self._create_indexes()
        print("Connected to MongoDB")

    async def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

    async def _create_indexes(self):
        await self.db.users.create_index("discord_id", unique=True)
        await self.db.social_accounts.create_index("platform")
        await self.db.social_accounts.create_index("account_name")
        await self.db.scheduled_posts.create_index("status")
        await self.db.scheduled_posts.create_index("scheduled_time")
        await self.db.activity_logs.create_index("discord_id")
        await self.db.activity_logs.create_index("timestamp")
        await self.db.bot_commands.create_index("name", unique=True)
        await self.db.published_posts.create_index("platform")
        await self.db.reply_actions.create_index("post_id")
        await self.db.delete_actions.create_index("post_id")  # actions de suppression

    # ************************ Users ************************
    async def get_or_create_user(self, discord_id: str, discord_username: str) -> User:
        user_dict = await self.db.users.find_one({"discord_id": discord_id})
        if user_dict:
            return User(**user_dict)
        user = User(discord_id=discord_id, discord_username=discord_username)
        result = await self.db.users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
        user.id = result.inserted_id
        return user

    # ************************ Social Accounts ************************
    async def add_social_account(
        self,
        platform: PlatformType,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        encrypted_access = encryption_handler.encrypt_token(access_token)
        encrypted_refresh = encryption_handler.encrypt_token(refresh_token) if refresh_token else None

        account = SocialMediaAccount(
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            tokens={
                "access_token": encrypted_access,
                "refresh_token": encrypted_refresh,
                "expires_at": expires_at,
            }
        )
        result = await self.db.social_accounts.insert_one(account.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    async def get_social_account(self, account_id: str) -> Optional[SocialMediaAccount]:
        acc = await self.db.social_accounts.find_one({"_id": ObjectId(account_id)})
        return SocialMediaAccount(**acc) if acc else None

    async def get_all_social_accounts(self) -> List[SocialMediaAccount]:
        accounts = []
        async for acc in self.db.social_accounts.find({"is_active": True}):
            accounts.append(SocialMediaAccount(**acc))
        return accounts

    async def get_tokens(self, account_id: str) -> Optional[Dict[str, Any]]:
        
        account = await self.get_social_account(account_id)
        if not account:
            return None
        return {
            "access_token": encryption_handler.decrypt_token(account.tokens.access_token),
            "refresh_token": encryption_handler.decrypt_token(account.tokens.refresh_token)
            if account.tokens.refresh_token else None,
            "expires_at": account.tokens.expires_at
        }

    # ************************ Scheduled Posts ************************
    async def create_scheduled_post(self, post: ScheduledPost) -> str:
        result = await self.db.scheduled_posts.insert_one(post.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    async def get_pending_posts(self, before_time: datetime) -> List[ScheduledPost]:
        query = {
            "status": PostStatus.SCHEDULED.value,
            "scheduled_time": {"$lte": before_time},
            "attempts": {"$lt": 3},
        }
        posts = []
        async for post in self.db.scheduled_posts.find(query).sort("scheduled_time", 1):
            posts.append(ScheduledPost(**post))
        return posts

    async def update_post_status(
        self, post_id: str, status: PostStatus,
        error_message: Optional[str] = None
    ) -> bool:
        update_data = {"status": status.value}
        if error_message:
            update_data["error_message"] = error_message
        if status == PostStatus.PUBLISHED:
            update_data["published_at"] = datetime.now(timezone.utc)
        result = await self.db.scheduled_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data, "$inc": {"attempts": 1}}
        )
        return result.modified_count > 0

    # ************************ Published Posts ************************
    async def create_published_post(self, post: PublishedPost) -> str:
        """Ajoute un post déjà publié."""
        result = await self.db.published_posts.insert_one(post.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    async def get_published_posts(self, platform: Optional[PlatformType] = None) -> List[PublishedPost]:
        """Récupère les posts publiés (optionnellement filtrés par plateforme)."""
        query = {"platform": platform.value} if platform else {}
        posts = []
        async for p in self.db.published_posts.find(query).sort("published_at", -1):
            posts.append(PublishedPost(**p))
        return posts

    # ************************ Bot Commands ************************
    async def add_bot_command(self, name: str, description: str, args: Optional[List[str]] = None, category: Optional[str] = None) -> str:
        command = BotCommand(name=name, description=description, args=args or [], category=category)
        result = await self.db.bot_commands.insert_one(command.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    async def get_bot_command(self, name: str) -> Optional[BotCommand]:
        cmd = await self.db.bot_commands.find_one({"name": name})
        return BotCommand(**cmd) if cmd else None

    async def get_all_bot_commands(self) -> List[BotCommand]:
        commands = []
        async for c in self.db.bot_commands.find().sort("created_at", 1):
            commands.append(BotCommand(**c))
        return commands

    # ************************ Reply Actions ************************
    async def log_reply_action(self, platform: PlatformType, post_id: str, comment: str, replied_by_discord_id: str, success: bool = True, error_message: Optional[str] = None) -> str:

        action = ReplyAction(
            platform=platform,
            post_id=post_id,
            comment=comment,
            replied_by_discord_id=replied_by_discord_id,
            executed_at=datetime.now(timezone.utc),
            success=success,
            error_message=error_message
        )
        result = await self.db.reply_actions.insert_one(action.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    async def get_replies_by_post(self, post_id: str) -> List[ReplyAction]:
        replies = []
        async for r in self.db.reply_actions.find({"post_id": post_id}).sort("executed_at", -1):
            replies.append(ReplyAction(**r))
        return replies

 # ************************ Delete (suppression) ************************
    async def delete_post(self, post_id: str, deleted_by_discord_id: str, platform: Optional[PlatformType] = None) -> Dict[str, Any]:
    # 1) tenter suppression dans published_posts
        query_pub = {"_id": ObjectId(post_id)} if ObjectId.is_valid(post_id) else {"post_id": post_id}
        deleted = False
        location = None
        error = None

        try:
               res = await self.db.published_posts.delete_one(query_pub)
               if res.deleted_count > 0:
                   deleted = True
                   location = "published"
        except Exception as e:
               error = str(e)

    # 2) si pas supprimé, tenter dans scheduled_posts
        if not deleted:
           try:
               res2 = await self.db.scheduled_posts.delete_one({"_id": ObjectId(post_id)})
               if res2.deleted_count > 0:
                deleted = True
                location = "scheduled"
           except Exception:
            try:
                res3 = await self.db.scheduled_posts.delete_one({"_id": post_id})  # fallback string id
                if res3.deleted_count > 0:
                    deleted = True
                    location = "scheduled"
            except Exception as e:
                error = str(e)

 
        return {"deleted": deleted, "location": location, "error": error}


    # ************************ Logs ************************
    async def log_command(
        self,
        discord_id: str,
        bot_command_id: Optional[str],
        platform: Optional[PlatformType] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        log = CommandLog(
            discord_id=discord_id,
            bot_command_id=bot_command_id,
            platform=platform or PlatformType.FACEBOOK,  # par défaut si tu veux forcer un value; adapte si nécessaire
            success=success,
            error_message=error_message
        )
        await self.db.command_logs.insert_one(log.model_dump(by_alias=True, exclude={"id"}))

    async def log_activity(
        self,
        discord_id: str,
        bot_command_id: Optional[str] = None,
        social_account_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        log = ActivityLog(
            discord_id=discord_id,
            bot_command_id=bot_command_id,
            social_account_id=social_account_id,
            details=details or {}
        )
        await self.db.activity_logs.insert_one(log.model_dump(by_alias=True, exclude={"id"}))


db_handler = MongoDBHandler()



"""""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from .model import (
    User, SocialMediaAccount, ScheduledPost,
    CommandLog, ActivityLog, PlatformType, PostStatus
)
from .encryption import encryption_handler


class MongoDBHandler:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    # ************************connection a mongo**************************
    async def connect(self):
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[os.getenv("MONGODB_DATABASE", "media_tracker")]
        await self._create_indexes()
        print("Connected to MongoDB")

    async def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

    async def _create_indexes(self):
        await self.db.users.create_index("discord_id", unique=True)
        await self.db.social_accounts.create_index("platform")
        await self.db.social_accounts.create_index("account_name")
        await self.db.scheduled_posts.create_index("status")
        await self.db.scheduled_posts.create_index("scheduled_time")
        await self.db.activity_logs.create_index("discord_id")
        await self.db.activity_logs.create_index("timestamp")

    #*********************user***********

    async def get_or_create_user(self, discord_id: str, discord_username: str) -> User:
        user_dict = await self.db.users.find_one({"discord_id": discord_id})
        if user_dict:
            return User(**user_dict)
        user = User(discord_id=discord_id, discord_username=discord_username)
        result = await self.db.users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
        user.id = result.inserted_id
        return user

    # ******************réseau sociaux****************************

    async def add_social_account(
        self,
        platform: PlatformType,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        
        encrypted_access = encryption_handler.encrypt_token(access_token)
        encrypted_refresh = encryption_handler.encrypt_token(refresh_token) if refresh_token else None

        account = SocialMediaAccount(
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            tokens={
                "access_token": encrypted_access,
                "refresh_token": encrypted_refresh,
                "expires_at": expires_at,
            }
        )

        result = await self.db.social_accounts.insert_one(
            account.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def get_social_account(self, account_id: str) -> Optional[SocialMediaAccount]:
        from bson import ObjectId
        acc = await self.db.social_accounts.find_one({"_id": ObjectId(account_id)})
        return SocialMediaAccount(**acc) if acc else None

    async def get_all_social_accounts(self) -> List[SocialMediaAccount]:
        accounts = []
        async for acc in self.db.social_accounts.find({"is_active": True}):
            accounts.append(SocialMediaAccount(**acc))
        return accounts

    async def get_tokens(self, account_id: str) -> Optional[Dict[str, Any]]:
       
        account = await self.get_social_account(account_id)
        if not account:
            return None
        return {
            "access_token": encryption_handler.decrypt_token(account.tokens.access_token),
            "refresh_token": encryption_handler.decrypt_token(account.tokens.refresh_token)
            if account.tokens.refresh_token else None,
            "expires_at": account.tokens.expires_at
        }

    # ***************scheduled post***************************

    async def create_scheduled_post(self, post: ScheduledPost) -> str:
        result = await self.db.scheduled_posts.insert_one(
            post.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)

    async def get_pending_posts(self, before_time: datetime) -> List[ScheduledPost]:

        query = {
            "status": PostStatus.SCHEDULED.value,
            "scheduled_time": {"$lte": before_time},
            "attempts": {"$lt": 3},
        }
        posts = []
        async for post in self.db.scheduled_posts.find(query).sort("scheduled_time", 1):
            posts.append(ScheduledPost(**post))
        return posts

    async def update_post_status(
        self, post_id: str, status: PostStatus,
        error_message: Optional[str] = None
    ) -> bool:
        from bson import ObjectId
        update_data = {"status": status.value}
        if error_message:
            update_data["error_message"] = error_message
        if status == PostStatus.PUBLISHED:
            update_data["published_at"] = datetime.utcnow()
        result = await self.db.scheduled_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data, "$inc": {"attempts": 1}}
        )
        return result.modified_count > 0

    # *******************loging**********************

    async def log_command(
        self, discord_id: str, command_name: str,
        command_args: Dict[str, Any] = None,
        success: bool = True, error_message: Optional[str] = None
    ):
        log = CommandLog(
            discord_id=discord_id,
            command_name=command_name,
            command_args=command_args or {},
            success=success,
            error_message=error_message
        )
        await self.db.command_logs.insert_one(log.model_dump(by_alias=True, exclude={"id"}))

    async def log_activity(
        self, discord_id: str, action: str,
        social_account_id: Optional[str] = None,
        platform: Optional[PlatformType] = None,
        details: Dict[str, Any] = None
    ):
        log = ActivityLog(
            discord_id=discord_id,
            action=action,
            social_account_id=social_account_id,
            platform=platform,
            details=details or {}
        )
        await self.db.activity_logs.insert_one(log.model_dump(by_alias=True, exclude={"id"}))



db_handler = MongoDBHandler()
"""