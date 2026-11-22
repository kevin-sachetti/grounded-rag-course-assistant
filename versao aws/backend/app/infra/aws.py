"""Clientes da AWS, criados uma vez e reaproveitados entre chamadas da Lambda."""
from functools import lru_cache

import boto3

from app.infra.config import settings


@lru_cache
def dynamodb():
    return boto3.resource("dynamodb", region_name=settings.aws_region)


@lru_cache
def s3():
    return boto3.client("s3", region_name=settings.aws_region)


@lru_cache
def s3_public():
    """S3 usado só para gerar os endereços de envio que o navegador vai usar."""
    if settings.aws_public_endpoint_url:
        return boto3.client(
            "s3", region_name=settings.aws_region, endpoint_url=settings.aws_public_endpoint_url
        )
    return s3()


@lru_cache
def lambda_client():
    return boto3.client("lambda", region_name=settings.aws_region)


@lru_cache
def cognito():
    return boto3.client("cognito-idp", region_name=settings.aws_region)


def table(name: str):
    return dynamodb().Table(name)
