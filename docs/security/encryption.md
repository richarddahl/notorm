# Encryption

The Uno Security Framework provides comprehensive encryption functionality for protecting sensitive data in your applications.

## Overview

The encryption component includes:

- **Field-level encryption**: Encrypt specific fields in your models
- **Data-at-rest encryption**: Encrypt data stored in databases or files
- **Key management**: Manage encryption keys securely

## Configuration

Encryption is configured through the `EncryptionConfig` class:

```python
from uno.security.config import EncryptionConfig, EncryptionAlgorithm, KeyManagementType

encryption_config = EncryptionConfig(
    algorithm=EncryptionAlgorithm.AES_GCM,
    key_management=KeyManagementType.VAULT,
    key_rotation_days=90,
    data_at_rest_encryption=True,
    data_in_transit_encryption=True,
    field_level_encryption=True,
    encrypted_fields=["password", "ssn", "credit_card", "api_key"],
    key_vault_url="https://vault.example.com",
    key_identifier="main-encryption-key"
)
```

Available encryption algorithms:

- `AES_GCM`: AES in Galois/Counter Mode (recommended for most cases)
- `AES_CBC`: AES in Cipher Block Chaining mode
- `CHACHA20_POLY1305`: ChaCha20-Poly1305
- `RSA`: RSA asymmetric encryption (for special cases)

Available key management types:

- `LOCAL`: Local key management (for development)
- `VAULT`: HashiCorp Vault
- `AWS_KMS`: AWS Key Management Service
- `AZURE_KEY_VAULT`: Azure Key Vault
- `GCP_KMS`: Google Cloud Key Management Service

## Using Encryption

### Basic Encryption and Decryption

```python
from uno.security import SecurityManager
from uno.security.config import SecurityConfig

# Create a security manager
security_manager = SecurityManager(SecurityConfig())

# Encrypt data
encrypted_data = security_manager.encrypt("sensitive data")
print(encrypted_data)  # Base64-encoded encrypted data

# Decrypt data
decrypted_data = security_manager.decrypt(encrypted_data)
print(decrypted_data)  # "sensitive data"

# Encrypt with context
encrypted_with_context = security_manager.encrypt(
    "sensitive data", 
    context={"purpose": "authentication"}
)

# Decrypt with the same context
decrypted_with_context = security_manager.decrypt(
    encrypted_with_context, 
    context={"purpose": "authentication"}
)
```

### Field-Level Encryption

Field-level encryption allows you to encrypt specific fields in your models:

```python
# Encrypt a field
encrypted_ssn = security_manager.encrypt_field("ssn", "123-45-6789")

# Decrypt a field
decrypted_ssn = security_manager.decrypt_field("ssn", encrypted_ssn)

# Encrypt multiple fields in a dictionary
user_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "ssn": "123-45-6789",
    "credit_card": "4111-1111-1111-1111"
}

from uno.security.encryption import FieldEncryption
field_encryption = FieldEncryption(security_manager.encryption_manager)
encrypted_data = field_encryption.encrypt_dict(user_data)
# Only ssn and credit_card will be encrypted

# Decrypt the dictionary
decrypted_data = field_encryption.decrypt_dict(encrypted_data)
```

### Model Encryption

You can also encrypt entire models:

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    ssn: str
    credit_card: str
    
    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "ssn": self.ssn,
            "credit_card": self.credit_card
        }

# Create a user
user = User(
    name="John Doe",
    email="john@example.com",
    ssn="123-45-6789",
    credit_card="4111-1111-1111-1111"
)

# Encrypt the model
encrypted_user = field_encryption.encrypt_model(user)
# Only ssn and credit_card will be encrypted

# Decrypt the model
decrypted_user = field_encryption.decrypt_model(encrypted_user)
```

### Encrypted Field Wrapper

For more control over field encryption, you can use the `EncryptedField` wrapper:

```python
from uno.security.encryption.field import EncryptedField

# Create an encrypted field
ssn_field = EncryptedField(
    value="123-45-6789",
    field_name="ssn",
    entity_type="User"
)

# Set the encryption manager
ssn_field.set_encryption_manager(security_manager.encryption_manager)

# Encrypt the field
encrypted_field = ssn_field.encrypt()
print(encrypted_field)  # EncryptedField(field_name=ssn, is_encrypted=True)

# Get the value (automatically decrypts if necessary)
value = encrypted_field.get_value()
print(value)  # "123-45-6789"

# Explicitly decrypt the field
decrypted_field = encrypted_field.decrypt()
print(decrypted_field.value)  # "123-45-6789"
```

## Key Management

### Local Key Management

Local key management is the default for development environments. It stores keys on the local filesystem:

```python
from uno.security.encryption.local_key_manager import LocalKeyManager

key_manager = LocalKeyManager(encryption_config)

# Get the current key
current_key = key_manager.get_current_key()

# Rotate keys
key_manager.rotate_keys()
```

### Vault Key Management

For production environments, you should use a secure key management system like HashiCorp Vault:

```python
from uno.security.encryption.vault_key_manager import VaultKeyManager

vault_manager = VaultKeyManager(
    encryption_config,
    vault_url="https://vault.example.com",
    token="vault-token"
)

# Get the current key
current_key = vault_manager.get_current_key()

# Rotate keys
vault_manager.rotate_keys()
```

## Encryption Providers

The framework includes several encryption providers that implement different algorithms:

### AES Encryption

```python
from uno.security.encryption.aes import AESEncryption

# AES-GCM (Authenticated Encryption)
aes_gcm = AESEncryption(mode="GCM")

# Encrypt data
encrypted = aes_gcm.encrypt("sensitive data")

# Decrypt data
decrypted = aes_gcm.decrypt(encrypted)

# AES-CBC
aes_cbc = AESEncryption(mode="CBC")
```

### RSA Encryption

```python
from uno.security.encryption.rsa import RSAEncryption

rsa = RSAEncryption(key_size=2048)

# Encrypt data
encrypted = rsa.encrypt("sensitive data")

# Decrypt data
decrypted = rsa.decrypt(encrypted)

# Get the public key in PEM format
public_key_pem = rsa.get_public_key_pem()
```

## Best Practices

1. **Use AES-GCM**: AES-GCM provides both confidentiality and integrity protection.
2. **Rotate keys regularly**: Rotate encryption keys regularly to limit the impact of a key compromise.
3. **Use a secure key management system**: For production, use a secure key management system like HashiCorp Vault.
4. **Encrypt sensitive fields**: Encrypt sensitive fields like passwords, social security numbers, and credit card numbers.
5. **Use different keys for different purposes**: Use different encryption keys for different purposes.
6. **Include context in encryption**: When possible, include context in encryption to prevent attacks.
7. **Keep encryption keys secure**: Ensure that encryption keys are stored securely and accessed only by authorized users.
8. **Back up encryption keys**: Back up encryption keys securely to prevent data loss.
9. **Monitor key usage**: Monitor encryption key usage and alert on suspicious activity.
10. **Test encryption and decryption**: Thoroughly test encryption and decryption to ensure that data can be recovered.