"""
PyObjectId
- Classe personnalisée pour gérer les ObjectId de MongoDB avec Pydantic.
- Assure une sérialisation JSON correcte des ObjectId.

- Enumération des plateformes sociales supportées : LINKEDIN, TIKTOK, FACEBOOK, INSTAGRAM.

- Enumération des statuts possibles pour un post : SCHEDULED, PUBLISHED, FAILED, CANCELLED.(pour scheduler)

PlatformTokens
- Modèle pour stocker les tokens d'accès aux API des plateformes.
- Contient access_token, refresh_token, date d'expiration et scope.
- Les tokens sont encryptés avec la fonction que j'ai créer dans src/utils/database/encryption

SocialMediaAccount
- Représente un compte connecté sur une plateforme sociale.
- Contient l'id MongoDB, le nom du compte, la plateforme, les tokens,
  la date de connexion et le dernier rafraîchissement.
- Champ is_active pour indiquer si le compte est actif.

User
- Représente un utilisateur Discord.
- Contient l'id MongoDB, l'id et le nom Discord, le rôle (member/admin),
  la date de création et de dernière mise à jour. 

ScheduledPost
- Modèle pour un post programmé sur une plateforme sociale.
- Contient l'id MongoDB, le compte social associé, l'utilisateur qui a demandé,
  la plateforme, le contenu, les médias, la date de publication prévue et le statut.
- Suivi des erreurs et des tentatives de publication.

CommandLog
- Enregistre les commandes exécutées par les utilisateurs Discord.
- Contient les arguments de la commande, le succès ou l'échec, et un message d'erreur si besoin.
- Permet de garder un historique pour débogage ou statistiques.

ActivityLog
- Suit les actions importantes des utilisateurs et du bot.
- Contient l'id MongoDB, l'utilisateur, l'action effectuée, le compte social concerné,
  la plateforme et des détails optionnels.
- Permet de créer un historique des événements pour audit ou analyse.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId




class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema

        def validate(value):
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError("Invalid ObjectId")

        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(validate),
        ])

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}




class PlatformType(str, Enum):
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"




class PlatformTokens(BaseModel):
    access_token: str  # encrypted
    refresh_token: Optional[str] = None  # encrypted
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None

    model_config = ConfigDict(json_encoders={ObjectId: str})


class SocialMediaAccount(BaseModel):
 
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    platform: PlatformType
    account_name: str
    account_id: Optional[str] = None  # ID sur la plateforme
    tokens: PlatformTokens
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_refresh: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class User(BaseModel):

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    discord_id: str
    discord_username: str
    role: Optional[str] = "member"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class ScheduledPost(BaseModel):

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    social_account_id: str  # référence vers SocialMediaAccount
    requested_by_discord_id: str
    platform: PlatformType
    content: str
    media_urls: List[str] = []
    scheduled_time: datetime
    status: PostStatus = PostStatus.SCHEDULED
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class CommandLog(BaseModel):
  
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    discord_id: str
    command_name: str
    command_args: Dict[str, Any] = {}
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class ActivityLog(BaseModel):

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    discord_id: str
    action: str  # ex: post_scheduled, post_published, page_connected
    social_account_id: Optional[str] = None
    platform: Optional[PlatformType] = None
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
