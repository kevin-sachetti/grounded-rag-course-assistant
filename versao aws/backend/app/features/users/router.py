from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.features import usage
from app.features.users import service
from app.infra.auth import current_user
from app.infra.config import settings

router = APIRouter(prefix="/me", tags=["usuário"])


def active_user(user_id: str = Depends(current_user)) -> dict:
    """Dependência de todas as rotas: o registro do usuário, com o último acesso em dia."""
    user = service.get_or_create(user_id)
    service.touch(user)
    return user


class Me(BaseModel):
    """O que a interface precisa saber do usuário: termos, limites e situação do mês."""

    terms_accepted: bool
    storage_used_bytes: int
    storage_limit_bytes: int
    questions_today: int
    questions_per_day: int
    inactivity_days: int
    month_blocked: bool


@router.get("", response_model=Me)
def me(user: dict = Depends(active_user)):
    return Me(
        terms_accepted=bool(user.get("terms_accepted_at")),
        storage_used_bytes=user.get("storage_bytes", 0),
        storage_limit_bytes=service.storage_limit_bytes(),
        questions_today=service.questions_today(user),
        questions_per_day=settings.questions_per_day,
        inactivity_days=settings.inactivity_days,
        month_blocked=usage.is_blocked(),
    )


@router.post("/terms", status_code=status.HTTP_204_NO_CONTENT)
def accept_terms(user: dict = Depends(active_user)):
    service.accept_terms(user["user_id"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user: dict = Depends(active_user)):
    """Exclui a conta e tudo o que ela tem. Não tem volta."""
    service.delete_account(user["user_id"])
