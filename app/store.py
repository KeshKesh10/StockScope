from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    return value


def _to_dynamo(value: Any) -> Any:
    if isinstance(value, list):
        return [_to_dynamo(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamo(item) for key, item in value.items()}
    if isinstance(value, float):
        # DynamoDB numeric attributes require Decimal instead of float.
        return Decimal(str(value))
    return value


class InMemoryStore:
    def __init__(self):
        self.users_by_id: dict[str, dict[str, Any]] = {}
        self.user_ids_by_username: dict[str, str] = {}
        self.favorites: dict[str, dict[str, dict[str, Any]]] = {}
        self.signups: dict[str, dict[str, Any]] = {}

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.users_by_id.get(user_id)

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        user_id = self.user_ids_by_username.get(username.lower())
        if not user_id:
            return None
        return self.users_by_id.get(user_id)

    def create_user(self, username: str, password_hash: str) -> dict[str, Any] | None:
        key = username.lower()
        if key in self.user_ids_by_username:
            return None

        user_id = str(uuid4())
        item = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "created_at": _iso_now(),
        }
        self.users_by_id[user_id] = item
        self.user_ids_by_username[key] = user_id
        return item

    def add_favorite(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ticker = str(payload["ticker"]).upper()
        user_favorites = self.favorites.setdefault(user_id, {})
        if ticker in user_favorites:
            raise ValueError("Ticker is already in favorites")

        item = {
            "ticker": ticker,
            "name": payload.get("name"),
            "industry": payload.get("industry"),
            "pe_ratio": payload.get("pe_ratio"),
            "growth_rate": payload.get("growth_rate"),
            "growth_over_pe": payload.get("growth_over_pe"),
            "analyst_target_price": payload.get("analyst_target_price"),
            "created_at": _iso_now(),
        }
        user_favorites[ticker] = item
        return item

    def list_favorites(self, user_id: str, industry: str | None = None) -> list[dict[str, Any]]:
        items = list(self.favorites.get(user_id, {}).values())
        if industry:
            check = industry.lower()
            items = [item for item in items if check in str(item.get("industry", "")).lower()]
        return sorted(items, key=lambda item: item["ticker"])

    def delete_favorite(self, user_id: str, ticker: str) -> bool:
        user_favorites = self.favorites.get(user_id, {})
        key = ticker.upper()
        if key not in user_favorites:
            return False
        del user_favorites[key]
        return True

    def create_signup(self, payload: dict[str, Any]) -> dict[str, Any]:
        signup_id = str(uuid4())
        item = {
            "signup_id": signup_id,
            "name": payload["name"],
            "email": payload["email"],
            "phone": payload["phone"],
            "category": payload["category"],
            "created_at": _iso_now(),
        }
        self.signups[signup_id] = item
        return item

    def list_signups(self, category: str | None = None) -> list[dict[str, Any]]:
        items = list(self.signups.values())
        if category:
            target = category.lower()
            items = [item for item in items if str(item.get("category", "")).lower() == target]
        return sorted(items, key=lambda item: item["created_at"], reverse=True)


class DynamoDBStore:
    def __init__(
        self,
        dynamodb_resource,
        users_table: str,
        favorites_table: str,
        signups_table: str,
    ):
        self.users = dynamodb_resource.Table(users_table)
        self.favorites = dynamodb_resource.Table(favorites_table)
        self.signups = dynamodb_resource.Table(signups_table)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        result = self.users.get_item(Key={"user_id": user_id})
        return _normalize(result.get("Item"))

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        result = self.users.query(
            IndexName="username-index",
            KeyConditionExpression=Key("username").eq(username.lower()),
            Limit=1,
        )
        items = result.get("Items", [])
        return _normalize(items[0]) if items else None

    def create_user(self, username: str, password_hash: str) -> dict[str, Any] | None:
        existing = self.get_user_by_username(username)
        if existing:
            return None

        item = {
            "user_id": str(uuid4()),
            "username": username.lower(),
            "password_hash": password_hash,
            "created_at": _iso_now(),
        }
        self.users.put_item(Item=item)
        return _normalize(item)

    def add_favorite(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ticker = str(payload["ticker"]).upper()
        industry = str(payload.get("industry") or "UNKNOWN").strip()

        item = {
            "user_id": user_id,
            "ticker": ticker,
            "name": payload.get("name"),
            "industry": industry,
            "industry_sort": f"{industry.upper()}#{ticker}",
            "pe_ratio": payload.get("pe_ratio"),
            "growth_rate": payload.get("growth_rate"),
            "growth_over_pe": payload.get("growth_over_pe"),
            "analyst_target_price": payload.get("analyst_target_price"),
            "created_at": _iso_now(),
        }

        try:
            self.favorites.put_item(
                Item=_to_dynamo(item),
                ConditionExpression="attribute_not_exists(ticker)",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise ValueError("Ticker is already in favorites") from exc
            raise

        return {
            "ticker": item["ticker"],
            "name": item.get("name"),
            "industry": item.get("industry"),
            "pe_ratio": item.get("pe_ratio"),
            "growth_rate": item.get("growth_rate"),
            "growth_over_pe": item.get("growth_over_pe"),
            "analyst_target_price": item.get("analyst_target_price"),
            "created_at": item.get("created_at"),
        }

    def list_favorites(self, user_id: str, industry: str | None = None) -> list[dict[str, Any]]:
        if industry:
            value = industry.strip().upper()
            response = self.favorites.query(
                IndexName="user-industry-index",
                KeyConditionExpression=Key("user_id").eq(user_id)
                & Key("industry_sort").begins_with(value),
            )
        else:
            response = self.favorites.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
            )

        items = [_normalize(item) for item in response.get("Items", [])]
        items.sort(key=lambda item: item.get("ticker", ""))

        mapped: list[dict[str, Any]] = []
        for item in items:
            mapped.append(
                {
                    "ticker": item.get("ticker"),
                    "name": item.get("name"),
                    "industry": item.get("industry"),
                    "pe_ratio": item.get("pe_ratio"),
                    "growth_rate": item.get("growth_rate"),
                    "growth_over_pe": item.get("growth_over_pe"),
                    "analyst_target_price": item.get("analyst_target_price"),
                    "created_at": item.get("created_at"),
                }
            )
        return mapped

    def delete_favorite(self, user_id: str, ticker: str) -> bool:
        try:
            self.favorites.delete_item(
                Key={"user_id": user_id, "ticker": ticker.upper()},
                ConditionExpression="attribute_exists(ticker)",
            )
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise

    def create_signup(self, payload: dict[str, Any]) -> dict[str, Any]:
        category = str(payload["category"]).strip()
        item = {
            "signup_id": str(uuid4()),
            "name": payload["name"],
            "email": payload["email"],
            "phone": payload["phone"],
            "category": category,
            "created_at": _iso_now(),
        }
        self.signups.put_item(Item=item)
        return _normalize(item)

    def list_signups(self, category: str | None = None) -> list[dict[str, Any]]:
        if category:
            response = self.signups.query(
                IndexName="category-index",
                KeyConditionExpression=Key("category").eq(category.strip().lower()),
            )
            items = response.get("Items", [])
        else:
            items = self.signups.scan().get("Items", [])

        normalized = [_normalize(item) for item in items]
        normalized.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return normalized
