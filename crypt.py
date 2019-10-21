from Crypto import Random as rnd
from Crypto.Hash import SHA256
from Crypto.Cipher import AES



def H(x):									# Method implementing SHA256 hash function
	key = bytes(str(x).encode('utf-8'))
	hash = SHA256.new()
	hash.digest_size = 16
	hash.update(key)
	return hash.digest()


def E(plaintext, key):						# AES block cipher encryption method
	plain = plaintext
	k = key
	iv = rnd.new().read(AES.block_size)
	cipher = AES.new(k, AES.MODE_CBC, iv)
	return iv + cipher.encrypt(plain)


def D(ciphertext, key):
	ciphertext = ciphertext
	key = key
	iv = ciphertext[:AES.block_size]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	plaintext = cipher.decrypt(ciphertext[AES.block_size:])
	return plaintext