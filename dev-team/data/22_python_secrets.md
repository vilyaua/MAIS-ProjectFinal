# Python secrets Module

## Overview

`secrets` generates cryptographically strong random values suitable for passwords, tokens, and security keys. Preferred over `random` for anything security-related.

## Generating Passwords

```python
import secrets
import string

alphabet = string.ascii_letters + string.digits + string.punctuation
password = "".join(secrets.choice(alphabet) for _ in range(16))
```

## Tokens

```python
token = secrets.token_hex(32)       # "a3f2...c8b1" (64 hex chars)
token = secrets.token_urlsafe(32)   # URL-safe base64 string
token = secrets.token_bytes(32)     # raw bytes
```

## Comparing Secrets Safely

```python
# Constant-time comparison — prevents timing attacks
secrets.compare_digest(user_input, stored_token)
```

## Best Practices

- Use `secrets` instead of `random` for passwords and tokens
- Use `secrets.choice()` instead of `random.choice()`
- Use `secrets.compare_digest()` for comparing tokens
- Minimum 16 characters for passwords, 32 bytes for tokens
