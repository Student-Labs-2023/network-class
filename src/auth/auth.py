from fastapi import FastAPI, Cookie, HTTPException, Depends
from fastapi.middleware import Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.main import app

#Обсудить с Арсением по поводу токенов

class OAuthMiddleware:
    def __init__(self, required_scopes: list = None):
        self.required_scopes = required_scopes

    async def __call__(self, request, call_next):
        token = request.cookies.get("oauth_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        if token not in valid_tokens:
            raise HTTPException(status_code=403, detail="Invalid token")

        request.state.user = valid_tokens[token]
        response = await call_next(request)
        return response


app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(OAuthMiddleware)


@app.get("/protected_endpoint/")
async def protected_endpoint(user: dict = Depends(OAuthMiddleware)):
    return {"message": "This is a protected endpoint.", "user_id": user["user_id"]}
