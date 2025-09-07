from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import os

# You can use your own secret key here
IV = b'1234567890123456'  # 16-byte IV

def encrypt_image(input_path, output_path, key):
    # Derive AES key from the provided key (already in bytes)
    aes_key = hashlib.sha256(key).digest()[:32]  # No need to encode since 'key' is already bytes
    
    # Perform encryption
    with open(input_path, 'rb') as f:
        image_data = f.read()
    cipher = AES.new(aes_key, AES.MODE_CBC, IV)
    encrypted_data = cipher.encrypt(pad(image_data, AES.block_size))
    
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)

def decrypt_image(input_path, output_path, key):
    try:
        # Derive AES key from the provided key
        aes_key = hashlib.sha256(key).digest()[:32]  # Derive key using SHA-256 hash

        with open(input_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Create AES cipher object for decryption
        cipher = AES.new(aes_key, AES.MODE_CBC, IV)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return True
    except Exception as e:
        print(f"Decryption error: {e}")
        return False
