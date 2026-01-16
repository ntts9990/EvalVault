from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Protocol

SECRET_REF_PREFIX = "secret://"


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> str: ...


class SecretProviderError(RuntimeError):
    pass


@dataclass
class EnvSecretProvider:
    def get_secret(self, name: str) -> str:
        value = os.environ.get(name)
        if value is None:
            raise SecretProviderError(f"Missing secret in environment: {name}")
        return value


@dataclass
class AwsSecretsManagerProvider:
    region_name: str | None = None

    def get_secret(self, name: str) -> str:
        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise SecretProviderError("boto3 is required for AWS Secrets Manager") from exc
        client = boto3.client("secretsmanager", region_name=self.region_name)
        response = client.get_secret_value(SecretId=name)
        if "SecretString" in response and response["SecretString"] is not None:
            return response["SecretString"]
        secret_binary = response.get("SecretBinary")
        if secret_binary is None:
            raise SecretProviderError("Empty secret value returned from AWS Secrets Manager")
        return base64.b64decode(secret_binary).decode("utf-8")


@dataclass
class GcpSecretManagerProvider:
    def get_secret(self, name: str) -> str:
        try:
            from google.cloud import secretmanager  # type: ignore
        except ImportError as exc:
            raise SecretProviderError(
                "google-cloud-secret-manager is required for GCP Secret Manager"
            ) from exc
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")


@dataclass
class VaultSecretProvider:
    def get_secret(self, name: str) -> str:
        try:
            import hvac  # type: ignore
        except ImportError as exc:
            raise SecretProviderError("hvac is required for Vault secret access") from exc
        client = hvac.Client()
        if not client.is_authenticated():
            raise SecretProviderError("Vault client authentication failed")
        response = client.secrets.kv.v2.read_secret_version(path=name)
        data = response.get("data", {}).get("data", {})
        if not data:
            raise SecretProviderError("Vault secret payload is empty")
        if "value" in data:
            return str(data["value"])
        if len(data) == 1:
            return str(next(iter(data.values())))
        raise SecretProviderError("Vault secret has multiple keys; specify 'value' key")


def is_secret_reference(value: str | None) -> bool:
    return bool(value) and value.startswith(SECRET_REF_PREFIX)


def parse_secret_reference(value: str) -> str:
    return value.removeprefix(SECRET_REF_PREFIX).strip()


def build_secret_provider(provider_name: str | None) -> SecretProvider:
    provider = (provider_name or "").strip().lower()
    if not provider:
        raise SecretProviderError("Secret provider is not configured.")
    if provider == "env":
        return EnvSecretProvider()
    if provider in {"aws", "aws-secrets-manager", "secretsmanager"}:
        return AwsSecretsManagerProvider(region_name=os.environ.get("AWS_REGION"))
    if provider in {"gcp", "gcp-secret-manager", "secretmanager"}:
        return GcpSecretManagerProvider()
    if provider in {"vault", "hashicorp-vault"}:
        return VaultSecretProvider()
    raise SecretProviderError(f"Unknown secret provider: {provider_name}")


def resolve_secret_reference(
    value: str,
    provider: SecretProvider,
    cache: dict[str, str] | None = None,
) -> str:
    secret_name = parse_secret_reference(value)
    if not secret_name:
        raise SecretProviderError("Secret reference must include a name.")
    if cache is not None and secret_name in cache:
        return cache[secret_name]
    secret_value = provider.get_secret(secret_name)
    if cache is not None:
        cache[secret_name] = secret_value
    return secret_value
