import asyncio
from .services.instagram_aiograpi import InstagramAiograpiService  
import os

async def main():
  
    insta = InstagramAiograpiService()

 
    USERNAME = "USERNAME"
    PASSWORD = "PSW"

    
    connected = await insta.login(USERNAME, PASSWORD)
    if not connected:
        print("Impossible de se connecter.")
        return
    print("Connexion réussie !")

    
    image_path = "Instagram.png"
    if not os.path.exists(image_path):
        print(f"L'image {image_path} est introuvable.")
        return

    caption = "Test automatique depuis aiograpi ! #test"


    print("Publication de la photo...")
    media = await insta.post_photo(image_path, caption)

    if media:
        print(f"Photo publiée avec succès ! ID: {media.pk}")
        print("URL :", insta.get_media_url(media))
    else:
        print("Échec de publication.")


    await insta.logout()


if __name__ == "__main__":
    asyncio.run(main())
