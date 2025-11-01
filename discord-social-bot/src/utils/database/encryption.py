import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
from typing import Optional
import base64
from dotenv import load_dotenv
load_dotenv()
class EncryptionHandler:
    def __init__(self, method: str = "fernet"):

        self.method = method
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY not found in environment variables.\n"
                "Generate one with:\n"
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        if self.method == "fernet":
            self._init_fernet(encryption_key)
        elif self.method == "aes-gcm":
            self._init_aes_gcm(encryption_key)
        else:
            raise ValueError(f"Unknown encryption method: {method}")
    
    def _init_fernet(self, encryption_key: str):

        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher = Fernet(encryption_key)
        print("Encryption: Fernet (AES-128-CBC + HMAC-SHA256)")
    
    def _init_aes_gcm(self, encryption_key: str):

        # Derive a proper 32-byte key using PBKDF2
        salt = os.getenv("ENCRYPTION_SALT", "default_salt_change_me").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.key = kdf.derive(encryption_key)
        print("Encryption: AES-256-GCM with PBKDF2 (100k iterations)")

    def encrypt(self, data: str) -> str:

        if not data:
            return ""
        
        if self.method == "fernet":
            return self._encrypt_fernet(data)
        else:
            return self._encrypt_aes_gcm(data)
    
    def _encrypt_fernet(self, data: str) -> str:
        
        encrypted = self.cipher.encrypt(data.encode())
        # Fernet already returns URL-safe base64, no need to encode again
        return encrypted.decode()
    
    def _encrypt_aes_gcm(self, data: str) -> str:
        
        # Generate random 96-bit nonce (recommended for GCM)
        nonce = secrets.token_bytes(12)
        
        # Create cipher
        cipher = AESGCM(self.key)
        
        # Encrypt (automatically includes authentication tag)
        ciphertext = cipher.encrypt(nonce, data.encode(), None)
        
        # Combine nonce + ciphertext
        combined = nonce + ciphertext
        
        # Return as base64
        return base64.urlsafe_b64encode(combined).decode()

    def decrypt(self, encrypted_data: str) -> Optional[str]:

        if not encrypted_data:
            return None
        
        try:
            if self.method == "fernet":
                return self._decrypt_fernet(encrypted_data)
            else:
                return self._decrypt_aes_gcm(encrypted_data)
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def _decrypt_fernet(self, encrypted_data: str) -> Optional[str]:
        
        # Fernet expects bytes
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def _decrypt_aes_gcm(self, encrypted_data: str) -> Optional[str]:
        
        # Decode from base64
        combined = base64.urlsafe_b64decode(encrypted_data.encode())
        
        # Split nonce and ciphertext
        nonce = combined[:12]
        ciphertext = combined[12:]
        
        # Create cipher
        cipher = AESGCM(self.key)
        
        # Decrypt and verify authentication tag
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode()

    def encrypt_token(self, token: str) -> str:
       
        return self.encrypt(token)

    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        
        return self.decrypt(encrypted_token)
    
    def rotate_key(self, old_key: str, new_key: str, encrypted_data: str) -> Optional[str]:

       
        old_cipher = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        
       
        decrypted = old_cipher.decrypt(encrypted_data.encode()).decode()
        
        
        return self.encrypt(decrypted)



def create_encryption_handler(method: str = None) -> EncryptionHandler:

    if method is None:
        method = os.getenv("ENCRYPTION_METHOD", "fernet")
    
    return EncryptionHandler(method=method)



encryption_handler = create_encryption_handler()


# function pour generer la clé
def generate_encryption_key() -> str:
    return Fernet.generate_key().decode()


def generate_salt() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
#main pour tester la fonction
'''''
if __name__ == "__main__":
    print("Test d'Encryption")
    print("=" * 60)
    
    # Générer une clé temporaire pour le test
    from cryptography.fernet import Fernet
    test_key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = test_key
    
    # Test avec Fernet
    print("\nTest avec Fernet (AES-128-CBC + HMAC)")
    print("-" * 60)
    
    handler = EncryptionHandler(method="fernet")
    
    # Message original
    message_original = "Mon token secret LinkedIn "
    print(f"Message original  : {message_original}")
    
    # Chiffrement
    message_chiffre = handler.encrypt(message_original)
    print(f"Message chiffré   : {message_chiffre}")
    
    # Déchiffrement
    message_dechiffre = handler.decrypt(message_chiffre)
    print(f"Message déchiffré : {message_dechiffre}")
    
    # Vérification
    if message_original == message_dechiffre:
        print("Encryption/Decryption : SUCCÈS")
    else:
        print("Encryption/Decryption : ÉCHEC")
    
    # Test avec AES-GCM (optionnel)
    print("\nTest avec AES-256-GCM")
    print("-" * 60)
    
    import base64, secrets
    os.environ["ENCRYPTION_SALT"] = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    handler_gcm = EncryptionHandler(method="aes-gcm")
    
    message_chiffre_gcm = handler_gcm.encrypt(message_original)
    print(f"Message chiffré   : {message_chiffre_gcm}")
    
    message_dechiffre_gcm = handler_gcm.decrypt(message_chiffre_gcm)
    print(f"Message déchiffré : {message_dechiffre_gcm}")
    
    if message_original == message_dechiffre_gcm:
        print("Encryption/Decryption : SUCCÈS")
    else:
        print("Encryption/Decryption : ÉCHEC")
    
    print("\n" + "=" * 60)
'''