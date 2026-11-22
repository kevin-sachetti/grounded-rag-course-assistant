"""Quem está fazendo o pedido: confere o token do Cognito e devolve o id do usuário.

O id (o "sub" do Cognito) é a chave de tudo no DynamoDB e no S3. Ele vem de
um token assinado pelo Cognito, então o usuário não tem como se passar por outro.
O e-mail nunca é usado como chave: fica só no Cognito, para o login.
"""
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException, status

from app.infra.config import settings


@lru_cache
def _jwks() -> jwt.PyJWKClient:
    issuer = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    return jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True)


def _issuer() -> str:
    return f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"


def current_user(authorization: str | None = Header(default=None)) -> str:
    """Dependência do FastAPI: o id do usuário dono do pedido."""
    if settings.auth_disabled:
        return settings.dev_user_id

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Entre na sua conta para continuar.")
    token = authorization.split(" ", 1)[1]
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        # Token de acesso do Cognito: confere assinatura, validade, emissor e aplicativo.
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=_issuer())
        if claims.get("token_use") != "access" or claims.get("client_id") != settings.cognito_client_id:
            raise jwt.InvalidTokenError("token de outro tipo ou de outro aplicativo")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada. Entre de novo.")
    return claims["sub"]
