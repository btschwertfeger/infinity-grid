# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from pydantic import BaseModel, computed_field, field_validator


class BotConfigDTO(BaseModel):
    """
    Data transfer object for the general bot configuration. These values are
    passed via CLI or environment variables.
    """

    # ==========================================================================
    # General attributes
    strategy: str
    exchange: str
    api_public_key: str
    api_secret_key: str
    name: str
    userref: int
    base_currency: str
    quote_currency: str
    fee: float | None = None
    dry_run: bool = False
    max_investment: float

    skip_price_timeout: bool = False

    # We expect these values to be set by the user via CLI or environment
    # variables. Cloup is handling the validation of these values.
    amount_per_grid: float
    interval: float
    n_open_buy_orders: int

    verbosity: int

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        """Validate the strategy value."""
        if value not in (valid_strategies := ("GridHODL", "GridSell", "SWING", "cDCA")):
            raise ValueError(f"Strategy must be one of: {', '.join(valid_strategies)}")
        return value

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, value: str) -> str:
        """Validate the exchange value."""
        if value.lower() != "kraken":
            raise ValueError("Currently only 'kraken' exchange is supported")
        return value

    @field_validator("userref")
    @classmethod
    def validate_userref(cls, value: int) -> int:
        """Validate userref is a positive integer."""
        if value < 0:
            raise ValueError("userref must be a non-negative integer")
        return value

    @field_validator("max_investment")
    @classmethod
    def validate_max_investment(cls, value: float) -> float:
        """Validate max_investment is positive."""
        if value <= 0:
            raise ValueError("max_investment must be greater than 0")
        return value

    @field_validator("amount_per_grid")
    @classmethod
    def validate_amount_per_grid(cls, value: float | None) -> float | None:
        """Validate amount_per_grid is positive if provided."""
        if value <= 0:
            raise ValueError("amount_per_grid must be greater than 0")
        return value

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: float | None) -> float | None:
        """Validate interval is between 0 and 1 if provided."""
        if value <= 0 or value >= 1:
            raise ValueError("interval must be between 0 and 1 (exclusive)")
        return value

    @field_validator("n_open_buy_orders")
    @classmethod
    def validate_n_open_buy_orders(cls, value: int | None) -> int | None:
        """Validate n_open_buy_orders is positive if provided."""
        if value <= 0:
            raise ValueError("n_open_buy_orders must be greater than 0")
        return value

    @field_validator("fee")
    @classmethod
    def validate_fee(cls, value: float | None) -> float | None:
        """Validate fee is between 0 and 1 if provided."""
        if value is not None and (value < 0 or value > 1):
            raise ValueError("fee must be between 0 and 1 (inclusive)")
        return value


class DBConfigDTO(BaseModel):
    sqlite_file: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_name: str = "infinity_grid"

    @field_validator("db_port")
    @classmethod
    def validate_db_port(cls, value: int | None) -> int | None:
        """Validate db_port is a positive integer if provided."""
        if value is not None and value <= 0:
            raise ValueError("db_port must be a positive integer")
        return value


class TelegramConfigDTO(BaseModel):
    """Pydantic model for Telegram notification configuration."""

    token: str | None = None
    chat_id: str | None = None
    thread_id: str | None = None

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str | None) -> str | None:
        """Validate Telegram bot token format."""
        if (value is not None and value.strip()) and (
            ":" not in value or len(value) < 20
        ):
            # Basic validation: should contain a colon and be reasonably long
            raise ValueError("Invalid Telegram bot token format")
        return value

    @computed_field
    def enabled(self) -> bool:
        """Return True if both token and chat_id are truthy values."""
        return bool(self.token and self.chat_id)


class NotificationConfigDTO(BaseModel):
    """Pydantic model for notification service configuration."""

    telegram: TelegramConfigDTO


class MetricsConfigDTO(BaseModel):
    """Pydantic model for metrics server configuration."""

    enabled: bool
    host: str
    port: int

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        """Validate port is within valid range."""
        if value < 1 or value > 65535:
            raise ValueError("port must be between 1 and 65535")
        return value
