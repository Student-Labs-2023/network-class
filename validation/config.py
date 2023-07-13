import os

# Настройки для аутентификации и проверки токена
AUTH0_JWKS_URI = os.getenv("AUTH0_JWKS_URI", "https://<auth0-tenant>.us.auth0.com/.well-known/jwks.json")
ISSUER = os.getenv("ISSUER", "dev-p5q3l0ydq4pvpv7c.us.auth0.com")
AUDIENCE = os.getenv("AUDIENCE", "https://nework-class-api")