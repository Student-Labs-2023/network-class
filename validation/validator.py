from functools import wraps
from flask import Flask, request, jsonify

from auth0_jwt_validator import (
    AccessTokenVerifier,
    MissingClaimError,
    InvalidClaimError,
)


app = Flask(__name__)


#Разобраться с AUTH0_JWKS_URI
from config import AUTH0_JWKS_URI, ISSUER, AUDIENCE
access_token_verifier = AccessTokenVerifier(AUTH0_JWKS_URI, ISSUER, AUDIENCE)


#Глобальный обработчик ошибок
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e)}), 500


def get_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith('Bearer '):
        return authorization.split()[1]
    return None


def validate_access_token_payload(access_token_payload: dict):
    required_fields = ['sub', 'exp']
    for field in required_fields:
        if field not in access_token_payload:
            raise MissingClaimError(f'Missing required claim: {field}')


def route_get_access_token_payload(f):
    @wraps(f)
    def _route_get_access_token_payload(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        bearer_token = get_bearer_token(authorization)
        if not bearer_token:
            raise InvalidClaimError("Missing access token")
        access_token_payload = access_token_verifier.verify(bearer_token)
        validate_access_token_payload(access_token_payload)
        return f(*args, **kwargs, access_token_payload=access_token_payload)

    return _route_get_access_token_payload


@app.get("/")
@route_get_access_token_payload
def index(access_token_payload: dict):
    return jsonify({"access_token_payload": access_token_payload})


if __name__ == '__main__':
    app.run()