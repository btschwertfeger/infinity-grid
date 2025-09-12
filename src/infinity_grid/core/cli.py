# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

from logging import DEBUG, INFO, WARNING, basicConfig, getLogger
from typing import Any

from click import FLOAT, INT, STRING, Context, echo, pass_context
from cloup import Choice, HelpFormatter, HelpTheme, Style, group, option, option_group
from cloup.constraints import Equal, If, IsSet, accept_none, require_all

from infinity_grid.models.configuration import (
    BotConfigDTO,
    DBConfigDTO,
    MetricsConfigDTO,
    NotificationConfigDTO,
    TelegramConfigDTO,
)


def print_version(ctx: Context, param: Any, value: Any) -> None:  # noqa: ANN401, ARG001
    """Prints the version of the package"""
    if not value or ctx.resilient_parsing:
        return
    from importlib.metadata import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
        version,
    )

    echo(version("infinity-grid"))
    ctx.exit()


def ensure_larger_than_zero(
    ctx: Context,
    param: Any,  # noqa: ANN401
    value: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Ensure the value is larger than 0"""
    if value <= 0:
        ctx.fail(f"Value for option '{param.name}' must be larger than 0!")
    return value


def ensure_larger_equal_zero(
    ctx: Context,
    param: Any,  # noqa: ANN401
    value: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Ensure the value is larger than 0"""
    if value is not None and value < 0:
        ctx.fail(f"Value for option '{param.name}' must be larger then or equal to 0!")
    return value


@group(
    context_settings={
        "auto_envvar_prefix": "INFINITY_GRID",
        "help_option_names": ["-h", "--help"],
    },
    formatter_settings=HelpFormatter.settings(
        theme=HelpTheme(
            invoked_command=Style(fg="bright_yellow"),
            heading=Style(fg="bright_white", bold=True),
            constraint=Style(fg="magenta"),
            col1=Style(fg="bright_yellow"),
        ),
    ),
    no_args_is_help=True,
)
@option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
@option(
    "--api-public-key",
    required=True,
    help="The Spot API key",
    type=STRING,
)
@option(
    "--api-secret-key",
    required=True,
    type=STRING,
    help="The Spot API secret key",
)
@option(
    "-v",
    "--verbose",
    count=True,
    help="Increase the verbosity of output. Use -vv for even more verbosity.",
)
@pass_context
def cli(ctx: Context, **kwargs: dict) -> None:
    """
    Command-line interface entry point
    """
    ctx.ensure_object(dict)
    ctx.obj |= kwargs
    ctx.obj["verbosity"] = ctx.obj.pop("verbose", 0)

    basicConfig(
        format="%(asctime)s %(levelname)8s | %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=INFO if ctx.obj["verbosity"] == 0 else DEBUG,
    )

    getLogger("requests").setLevel(WARNING)
    getLogger("urllib3").setLevel(WARNING)
    getLogger("websockets").setLevel(WARNING)

    if ctx.obj["verbosity"] > 1:
        getLogger("requests").setLevel(DEBUG)
        getLogger("websockets").setLevel(DEBUG)
        getLogger("kraken").setLevel(DEBUG)
    else:
        getLogger("websockets").setLevel(WARNING)
        getLogger("kraken").setLevel(WARNING)


@cli.command(
    context_settings={
        "auto_envvar_prefix": "INFINITY_GRID_RUN",
        "help_option_names": ["-h", "--help"],
    },
    formatter_settings=HelpFormatter.settings(
        theme=HelpTheme(
            invoked_command=Style(fg="bright_yellow"),
            heading=Style(fg="bright_white", bold=True),
            constraint=Style(fg="magenta"),
            col1=Style(fg="bright_yellow"),
        ),
    ),
)
@option_group(
    "Strategy Configuration",
    option(
        "--strategy",
        type=Choice(
            choices=(
                "cDCA",
                "GridHODL",
                "GridSell",
                "SWING",  # FIXME: rename to "Swing"
            ),
            case_sensitive=True,
        ),
        help="The strategy to run.",
        required=True,
    ),
    option(
        "--name",
        required=True,
        type=STRING,
        help="""
        The name of the instance. Can be any name that is used to differentiate
        between instances of the infinity-grid.
        """,
    ),
    option(
        "--exchange",
        type=Choice(choices=("Kraken",), case_sensitive=True),
        help="The exchange to trade on.",
        required=True,
    ),
    option(
        "--max-investment",
        required=False,
        type=FLOAT,
        default=10e10,
        show_default=True,
        callback=ensure_larger_than_zero,
        help="""
        The maximum investment, e.g. 1000 USD that the algorithm will manage.
        """,
    ),
    option(
        "--userref",
        required=True,
        type=INT,
        callback=ensure_larger_than_zero,
        help="""
        A reference number to identify the algorithm's orders. This can be a
        timestamp or any positive integer number. Use different userref's for
        different instances!
        """,
    ),
    option(
        "--fee",
        type=FLOAT,
        required=False,
        callback=ensure_larger_equal_zero,
        help="""
        The fee percentage to respect, e.g. '0.0026' for 0.26 %. This value does not
        change the actual paid fee! It is used to estimate order sizes. If not
        passed, the highest maker fee will be assumed.
        """,
    ),
)
@option_group(
    "Trading Pair Configuration",
    option(
        "--base-currency",
        required=True,
        type=STRING,
        help="The base currency.",
    ),
    option(
        "--quote-currency",
        required=True,
        type=STRING,
        help="The quote currency.",
    ),
)
@option_group(
    "Grid Strategy Options",
    option(
        "--amount-per-grid",
        type=FLOAT,
        help="The quote amount to use per interval.",
    ),
    option(
        "--interval",
        type=FLOAT,
        default=0.02,
        show_default=True,
        callback=ensure_larger_than_zero,
        help="The interval between orders (e.g. 0.02 equals 2%).",
    ),
    option(
        "--n-open-buy-orders",
        type=INT,
        default=3,
        show_default=True,
        callback=ensure_larger_than_zero,
        help="""
        The number of concurrent open buy orders e.g., ``5``. The number of
        always open buy positions specifies how many buy positions should be
        open at the same time. If the interval is defined to 2%, a number of 5
        open buy positions ensures that a rapid price drop of almost 10% that
        can be caught immediately.
        """,
    ),
    constraint=If(  # Useless if no further strategies are implemented
        Equal("strategy", "cDCA")
        | Equal("strategy", "GridHODL")
        | Equal("strategy", "GridSell")
        | Equal("strategy", "SWING"),
        then=require_all,
        else_=accept_none,
    ),
)
@option_group(
    "Additional options",
    option(
        "--skip-price-timeout",
        is_flag=True,
        default=False,
        help="""
        Skip checking if there was a price update in the last 10 minutes. By
        default, the bot will exit if no recent price data is available. This
        might be useful for assets that aren't traded that often.
        """,
    ),
    option(
        "--dry-run",
        required=False,
        is_flag=True,
        default=False,
        help="Enable dry-run mode which do not execute trades.",
    ),
)
@option_group(
    "General Database Configuration",
    option(
        "--db-name",
        type=STRING,
        default="infinity_grid",
        show_default=True,
        help="The database name.",
    ),
    option(
        "--sqlite-file",
        type=STRING,
        help="SQLite file to use as database.",
    ),
    option(
        "--in-memory",
        is_flag=True,
        default=False,
        show_default=True,
        help='Use an in-memory database (similar to --sqlite-file=":memory:").',
    ),
)
@option_group(
    "PostgreSQL Database Options",
    option(
        "--db-user",
        type=STRING,
        help="PostgreSQL DB user",
    ),
    option(
        "--db-password",
        type=STRING,
        help="PostgreSQL DB password",
    ),
    option(
        "--db-host",
        type=STRING,
        help="PostgreSQL DB host",
    ),
    option(
        "--db-port",
        type=STRING,
        help="PostgreSQL DB port",
    ),
    constraint=If(
        ~IsSet("sqlite_file") & ~IsSet("in_memory"),
        then=require_all,
        else_=accept_none,
    ),
)
@option_group(
    "Notification Options",
    option(
        "--telegram-token",
        required=False,
        type=STRING,
        help="The Telegram token to use.",
    ),
    option(
        "--telegram-chat-id",
        required=False,
        type=STRING,
        help="The telegram chat ID to use.",
    ),
    option(
        "--telegram-thread-id",
        required=False,
        type=STRING,
        help="The telegram thread ID to use.",
    ),
)
@option_group(
    "Metrics Server Options",
    option(
        "--metrics-enabled/--no-metrics-enabled",
        default=True,
        show_default=True,
        help="Enable or disable the metrics HTTP server.",
    ),
    option(
        "--metrics-host",
        type=STRING,
        default="127.0.0.1",
        show_default=True,
        help="Host address for the metrics server.",
    ),
    option(
        "--metrics-port",
        type=INT,
        default=8080,
        show_default=True,
        help="Port for the metrics server.",
    ),
)
@pass_context
def run(ctx: Context, **kwargs: dict[str, Any]) -> None:
    """Run the trading algorithm using the specified options."""
    # pylint: disable=import-outside-top-level
    import asyncio  # noqa: PLC0415

    from infinity_grid.core.engine import BotEngine  # noqa: PLC0415

    # Handle in-memory database option
    if kwargs.pop("in_memory", False):
        kwargs["sqlite_file"] = ":memory:"  # type: ignore[assignment]

    db_config = DBConfigDTO(
        sqlite_file=kwargs.pop("sqlite_file", None),
        db_user=kwargs.pop("db_user", None),
        db_password=kwargs.pop("db_password", None),
        db_host=kwargs.pop("db_host", None),
        db_port=kwargs.pop("db_port", None),
        db_name=kwargs.pop("db_name", "infinity_grid"),
    )
    notification_config = NotificationConfigDTO(
        telegram=TelegramConfigDTO(
            token=kwargs.pop("telegram_token", None),
            chat_id=kwargs.pop("telegram_chat_id", None),
            thread_id=kwargs.pop("telegram_thread_id", None),
        ),
    )
    metrics_config = MetricsConfigDTO(
        enabled=kwargs.pop("metrics_enabled"),
        host=kwargs.pop("metrics_host"),
        port=kwargs.pop("metrics_port"),
    )
    ctx.obj |= kwargs

    asyncio.run(
        BotEngine(
            bot_config=BotConfigDTO(**ctx.obj),
            db_config=db_config,
            notification_config=notification_config,
            metrics_config=metrics_config,
        ).run(),
    )
