# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""Unit tests for the configuration models."""

import pytest
from pydantic import ValidationError

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    NotificationConfigDTO,
    TelegramConfigDTO,
)

TOKEN = "test_token:12345678901234567890"  # noqa: S105
CHAT_ID = "1234567890"


class TestTelegramConfigDTO:
    def test_telegram_config_enabled_both_values(self) -> None:
        """Test TelegramConfigDTO enabled when both token and chat_id are provided."""
        config = TelegramConfigDTO(token=TOKEN, chat_id=CHAT_ID)

        assert config.enabled is True

    def test_telegram_config_disabled_missing_token(self) -> None:
        """Test TelegramConfigDTO disabled when token is missing."""
        config = TelegramConfigDTO(chat_id=CHAT_ID)

        assert config.enabled is False

    def test_telegram_config_disabled_missing_chat_id(self) -> None:
        """Test TelegramConfigDTO disabled when chat_id is missing."""
        config = TelegramConfigDTO(token=TOKEN)

        assert config.enabled is False

    def test_telegram_config_disabled_both_missing(self) -> None:
        """Test TelegramConfigDTO disabled when both values are missing."""
        config = TelegramConfigDTO()

        assert config.enabled is False

    def test_telegram_config_disabled_empty_values(self) -> None:
        """Test TelegramConfigDTO disabled when values are empty strings."""
        config = TelegramConfigDTO(token="", chat_id="")

        assert config.enabled is False

    def test_telegram_config_invalid_token(self) -> None:
        """Test TelegramConfigDTO with invalid token format."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramConfigDTO(token="invalid_token")  # Missing colon and too short

        assert "Invalid Telegram bot token format" in str(exc_info.value)


class TestBotConfigDTO:

    def test_bot_config_valid_strategy(self) -> None:
        """Test BotConfigDTO with valid strategy values."""
        valid_strategies = ["GridHODL", "GridSell", "SWING", "cDCA"]

        for strategy in valid_strategies:
            config = BotConfigDTO(
                strategy=strategy,
                exchange="kraken",
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=12345,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=1000.0,
                amount_per_grid=100.0,
                interval=0.02,
                n_open_buy_orders=5,
            )
            assert config.strategy == strategy

    def test_bot_config_invalid_strategy(self) -> None:
        """Test BotConfigDTO with invalid strategy value."""
        with pytest.raises(ValidationError) as exc_info:
            BotConfigDTO(
                strategy="InvalidStrategy",
                exchange="kraken",
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=12345,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=1000.0,
                amount_per_grid=100.0,
                interval=0.02,
                n_open_buy_orders=5,
            )

        assert "Strategy must be one of:" in str(exc_info.value)

    def test_bot_config_invalid_exchange(self) -> None:
        """Test BotConfigDTO with invalid exchange."""
        with pytest.raises(ValidationError) as exc_info:
            BotConfigDTO(
                strategy="GridHODL",
                exchange="binance",  # Invalid exchange
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=12345,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=1000.0,
                amount_per_grid=100.0,
                interval=0.02,
                n_open_buy_orders=5,
            )

        assert "Currently only 'kraken' exchange is supported" in str(exc_info.value)

    def test_bot_config_invalid_userref(self) -> None:
        """Test BotConfigDTO with negative userref."""
        with pytest.raises(ValidationError) as exc_info:
            BotConfigDTO(
                strategy="GridHODL",
                exchange="kraken",
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=-1,  # Invalid negative userref
                base_currency="BTC",
                quote_currency="USD",
                max_investment=1000.0,
                amount_per_grid=100.0,
                interval=0.02,
                n_open_buy_orders=5,
            )

        assert "userref must be a non-negative integer" in str(exc_info.value)

    def test_bot_config_invalid_max_investment(self) -> None:
        """Test BotConfigDTO with zero or negative max_investment."""
        with pytest.raises(ValidationError) as exc_info:
            BotConfigDTO(
                strategy="GridHODL",
                exchange="kraken",
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=12345,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=0.0,  # Invalid zero investment
                amount_per_grid=100.0,
                interval=0.02,
                n_open_buy_orders=5,
            )

        assert "max_investment must be greater than 0" in str(exc_info.value)

    def test_bot_config_invalid_interval(self) -> None:
        """Test BotConfigDTO with invalid interval values."""
        # Test interval >= 1
        with pytest.raises(ValidationError) as exc_info:
            BotConfigDTO(
                strategy="GridHODL",
                exchange="kraken",
                api_public_key="test_key",
                api_secret_key="test_secret",
                name="test_bot",
                userref=12345,
                base_currency="BTC",
                quote_currency="USD",
                max_investment=1000.0,
                amount_per_grid=100.0,
                interval=1.0,  # Invalid interval
                n_open_buy_orders=5,
            )

        assert "interval must be between 0 and 1 (exclusive)" in str(exc_info.value)


class TestDBConfigDTO:
    def test_db_config_invalid_port(self) -> None:
        """Test DBConfigDTO with invalid port values."""
        # Test non-numeric port
        with pytest.raises(ValidationError) as exc_info:
            DBConfigDTO(db_port=-123)

        assert "db_port must be a positive integer" in str(exc_info.value)


class TestNotificationConfigDTO:
    def test_notification_config(self) -> None:
        """Test NotificationConfigDTO with telegram config."""
        telegram_config = TelegramConfigDTO(token=TOKEN, chat_id=CHAT_ID)
        config = NotificationConfigDTO(telegram=telegram_config)

        assert config.telegram.enabled is True
