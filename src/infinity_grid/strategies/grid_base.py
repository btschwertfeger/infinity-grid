# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

"""
This module contains the base class for grid-based trading strategies.

All grid-based strategies should inherit from this class and implement
the required methods and override exiting ones as needed.
"""


import asyncio
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from logging import getLogger
from time import sleep
from typing import TYPE_CHECKING, Iterable, Self

from infinity_grid.core.event_bus import EventBus
from infinity_grid.core.state_machine import StateMachine, States
from infinity_grid.exceptions import BotStateError, UnknownOrderError
from infinity_grid.infrastructure.database import (
    Configuration,
    FutureOrders,
    Orderbook,
    PendingTXIDs,
    TSPState,
    UnsoldBuyOrderTXIDs,
)
from infinity_grid.interfaces.exchange import (
    IExchangeRESTService,
    IExchangeWebSocketService,
)
from infinity_grid.models.configuration import BotConfigDTO
from infinity_grid.models.exchange import (
    OnMessageSchema,
    OrderInfoSchema,
    TickerUpdateSchema,
)
from infinity_grid.services.database import DBConnect

if TYPE_CHECKING:

    from infinity_grid.models.exchange import AssetPairInfoSchema, ExchangeDomain

LOG = getLogger(__name__)


class GridStrategyBase:
    """
    Base class for grid-like strategies.

    This class is intended to be used as base class for subsequent strategies
    and contains lots of protected and private functions that might need to be
    disabled when being used in custom strategies that do not belong to
    GridHODL, GridSell, SWING, or CDCA.
    """

    def __init__(
        self,
        config: BotConfigDTO,
        event_bus: EventBus,
        state_machine: StateMachine,
        db: DBConnect,
    ) -> None:
        self._config: BotConfigDTO = config
        self._event_bus: EventBus = event_bus
        self._state_machine: StateMachine = state_machine
        self._ticker: float | None = None

        self._rest_api: IExchangeRESTService
        self.__ws_client: IExchangeWebSocketService
        self._exchange_domain: ExchangeDomain

        self._orderbook_table: Orderbook = Orderbook(self._config.userref, db)
        self._configuration_table: Configuration = Configuration(
            self._config.userref,
            db,
        )
        self._pending_txids_table: PendingTXIDs = PendingTXIDs(self._config.userref, db)
        self._unsold_buy_order_txids_table: UnsoldBuyOrderTXIDs = UnsoldBuyOrderTXIDs(
            self._config.userref,
            db,
        )
        self._future_orders_table: FutureOrders = FutureOrders(self._config.userref, db)
        # FIXME: not needed if tsp not activated
        self._tsp_state_table: TSPState = TSPState(
            self._config.userref,
            db,
            tsp_percentage=self._config.trailing_stop_profit,
        )
        db.init_db()

        # Tracks the last time a ticker message was received for checking
        # connectivity.
        self._last_price_time: datetime | None = None
        # Remember the last time when a status notification was sent to ensure
        # this only happens once an hour.
        self._last_status_update: datetime | None = None

        self._cost_decimals: int
        self._amount_per_grid_plus_fee: float

        # Store messages received before the algorithm is ready to trade.
        self._missed_messages: list[OnMessageSchema] = []
        self._ticker_channel_connected = False
        self._executions_channel_connected = False
        self._ready_to_trade = False

    async def run(self: Self) -> None:
        """
        Main entry point when starting a trading strategy.

        - Connects to the exchange API.
        - Checks exchange status and API key permissions.
        - Subscribes to the required WebSocket channels.
        - Runs the main loop.
        """
        # ======================================================================
        # Try to connect to the API, validate credentials and API key
        # permissions.
        ##
        self._rest_api = self.get_rest_adapter(
            self._config.exchange,
        )(
            api_public_key=self._config.api_public_key,
            api_secret_key=self._config.api_secret_key,
            state_machine=self._state_machine,
            base_currency=self._config.base_currency,
            quote_currency=self._config.quote_currency,
        )
        self._exchange_domain = self._rest_api.get_exchange_domain()

        self.__ws_client = self.get_websocket_adapter(
            self._config.exchange,
        )(
            api_public_key=self._config.api_public_key,
            api_secret_key=self._config.api_secret_key,
            event_bus=self._event_bus,
            state_machine=self._state_machine,
        )

        self._rest_api.check_exchange_status()
        self._rest_api.check_api_key_permissions()

        if self._state_machine.state == States.ERROR:
            raise BotStateError(
                "The algorithm was shut down by error during initialization!",
            )

        # ======================================================================
        # Start the websocket connection
        ##
        LOG.info("Starting the websocket connection...")
        await self.__ws_client.start()
        LOG.info("Websocket connection established!")

        # ======================================================================
        # Subscribe to the execution and ticker channels
        ##
        LOG.info("Subscribing to channels...")
        # FIXME: improve this to be more generic and not hardcoded at this place
        for subscription in {
            "Kraken": [
                {"channel": "ticker", "symbol": [self._rest_api.ws_symbol]},
                {
                    "channel": "executions",
                    # Snapshots are only required to check if the channel is
                    # connected. They are not used for any other purpose.
                    "snap_orders": True,
                    "snap_trades": True,
                },
            ],
        }[self._config.exchange]:
            await self.__ws_client.subscribe(subscription)  # type: ignore[arg-type]

        while True:
            try:
                last_hour = (now := datetime.now()) - timedelta(hours=1)

                if self._state_machine.state == States.RUNNING and (
                    self._last_price_time
                    and (
                        not self._last_status_update
                        or self._last_status_update < last_hour
                    )
                ):
                    # Send update once per hour
                    self.send_status_update()

                if (
                    not self._config.skip_price_timeout
                    and self._last_price_time
                    and self._last_price_time + timedelta(seconds=600) < now
                ):
                    LOG.error("No price update since 10 minutes - exiting!")
                    self._state_machine.transition_to(States.ERROR)
                    return

            except (
                Exception  # noqa: BLE001
            ) as exc:  # pylint: disable=broad-exception-caught
                LOG.error("Exception in main.", exc_info=exc)
                self._state_machine.transition_to(States.ERROR)
                return

            await asyncio.sleep(6)

    async def stop(self: Self) -> None:
        """Stop the WebSocket connection(s)."""
        await self.__ws_client.close()

    def on_message(self: Self, message: OnMessageSchema) -> None:  # noqa: C901
        """Handle incoming messages from the WebSocket connection(s)."""
        try:
            # ==================================================================
            # Initial setup
            if self._state_machine.state != States.RUNNING:
                if message.channel == "ticker" and not self._ticker_channel_connected:
                    self._ticker_channel_connected = True
                    # Set ticker the first time to have the ticker set during setup.
                    self.__on_ticker_update(message.ticker_data)
                    LOG.info("- Subscribed to ticker channel successfully!")

                elif (
                    message.channel == "executions"
                    and not self._executions_channel_connected
                ):
                    self._executions_channel_connected = True
                    LOG.info("- Subscribed to execution channel successfully!")

                if (
                    self._ticker_channel_connected
                    and self._executions_channel_connected
                    and not self._ready_to_trade
                ):
                    self.__prepare_for_trading()

                    # If there are any missed messages, process them now.
                    for msg in self._missed_messages:
                        self.on_message(msg)
                        self._missed_messages = [
                            m for m in self._missed_messages if m != msg
                        ]

                if not self._ready_to_trade:
                    if message.channel == "executions":
                        # If the algorithm is not ready to trade, store the
                        # executions to process them later.
                        self._missed_messages.append(message)

                    # Return here, until the algorithm is ready to trade. It is
                    # ready when the init/setup is done and the orderbook is
                    # updated/synced initially.
                    return

            # ==================================================================
            # Handle ticker and execution messages

            if message.channel == "ticker":
                self.__on_ticker_update(message.ticker_data)

            elif message.channel == "executions":
                if message.type != "update":
                    # Snapshot data is not interesting, as this is handled
                    # during sync with upstream.
                    return

                for execution in message.executions:
                    LOG.debug("Got execution: %s", execution)

                    if execution.exec_type == "new":
                        LOG.debug("Processing new order: '%s'", execution.order_id)
                        self._assign_order_by_txid(execution.order_id)

                    elif execution.exec_type == "filled":
                        LOG.debug("Processing filled order: '%s'", execution.order_id)
                        self.handle_filled_order_event(execution.order_id)

                    elif execution.exec_type in {"canceled", "expired"}:
                        LOG.debug(
                            "Processing cancelled order: '%s'",
                            execution.order_id,
                        )
                        self._handle_cancel_order(execution.order_id)

        except Exception as exc:  # noqa: BLE001
            LOG.error(msg="Exception while processing message.", exc_info=exc)
            self._state_machine.transition_to(States.ERROR)
            return

    @classmethod
    def get_rest_adapter(cls, exchange: str) -> type[IExchangeRESTService]:
        """Get the exchange REST adapter."""
        if exchange == "Kraken":
            from infinity_grid.adapters.exchanges.kraken import (  # pylint: disable=import-outside-toplevel # noqa: PLC0415
                KrakenExchangeRESTServiceAdapter,
            )

            return KrakenExchangeRESTServiceAdapter

        raise ValueError(
            f"Unsupported exchange for REST adapter: {exchange}",
        )

    @classmethod
    def get_websocket_adapter(cls, exchange: str) -> type[IExchangeWebSocketService]:
        if exchange == "Kraken":
            from infinity_grid.adapters.exchanges.kraken import (  # pylint: disable=import-outside-toplevel # noqa: PLC0415
                KrakenExchangeWebsocketServiceAdapter,
            )

            return KrakenExchangeWebsocketServiceAdapter

        raise ValueError(
            f"Unsupported exchange for Websocket adapter: {exchange}",
        )

    # ==========================================================================
    # Event handlers
    def __on_ticker_update(self, ticker_info: TickerUpdateSchema) -> None:
        if ticker_info.symbol != self._rest_api.ws_symbol:
            LOG.debug(
                "Ignoring ticker update for different symbol: %s",
                ticker_info.symbol,
            )
            return

        self._ticker = float(ticker_info.last)
        self._last_price_time = datetime.now()

        if self._state_machine.state == States.RUNNING:
            if self._unsold_buy_order_txids_table.count() != 0:
                self.__add_missed_sell_orders()

            self.__check_price_range()

    def __prepare_for_trading(self: Self) -> None:
        """
        This function gets triggered once during the setup of the algorithm. It
        prepares the algorithm for live trading by checking the asset pair
        parameters, syncing the local with the upstream orderbook, place missing
        sell orders that not get through because of e.g. "missing funds", and
        updating the orderbook.

        This function must be sync, since it must block until the setup is done.
        FIXME: The naming of the function is not ideal
        """
        LOG.info(
            "Preparing for trading by initializing and updating local orderbook...",
        )

        self._event_bus.publish(
            "notification",
            data={"message": f"✅ {self._config.name} is starting!"},
        )

        # ======================================================================

        # Check the fee and pair of the asset pair
        self.__retrieve_asset_information()

        # Append orders to local orderbook in case they are not saved yet
        self._assign_all_pending_transactions()

        # Try to place missing sell orders that not get through because of
        # "missing funds".
        self.__add_missed_sell_orders()

        # Update the orderbook, check for closed, filled, cancelled trades,
        # and submit new orders if necessary.
        try:
            self.__sync_order_book()
        except Exception as exc:
            message = f"Exception while updating the orderbook: {exc}: {traceback.format_exc()}"
            LOG.error(message)
            self._state_machine.transition_to(States.ERROR)
            raise BotStateError(message) from exc

        # Check if the configured amount per grid or the interval have changed,
        # requiring a cancellation of all open buy orders.
        self.__check_configuration_changes()

        # Everything is done, the bot is ready to trade live.
        self._ready_to_trade = True
        LOG.info("Algorithm is ready to trade!")

        # Checks if the open orders match the range and cancel if necessary. It
        # is the heart of this algorithm and gets triggered every time the price
        # changes.
        self.__check_price_range()
        self._state_machine.transition_to(States.RUNNING)

    # ==========================================================================
    # Setup methods

    def __retrieve_asset_information(self: Self) -> None:
        """
        Retrieve the asset pair information from the exchange.

        This includes:
        - Estimated fee
        - Cost decimals
        - Amount per grid plus + fee
        """
        LOG.info("- Retrieving asset pair information...")
        pair_info: AssetPairInfoSchema = self._rest_api.get_asset_pair_info()
        LOG.debug(pair_info)

        if self._config.fee is None:
            # This is the case if the '--fee' parameter was not passed, then we
            # take the highest maker fee.
            self._config.fee = float(pair_info.fees_maker[0][1]) / 100

        self._cost_decimals = pair_info.cost_decimals
        self._amount_per_grid_plus_fee = self._config.amount_per_grid * (
            1 + self._config.fee
        )

    def __update_orderbook_get_open_orders(self: Self) -> list[OrderInfoSchema]:
        """
        Retrieve all open orders from the upstream exchange that are related to
        the current trading pair.
        """
        LOG.info("  - Retrieving open orders from upstream...")

        return [
            order
            for order in self._rest_api.get_open_orders(userref=self._config.userref)
            if order.pair == self._rest_api.rest_altname
        ]

    def __update_order_book_handle_closed_order(
        self: Self,
        closed_order: OrderInfoSchema,
    ) -> None:
        """
        Gets executed when an order of the local orderbook was closed in the
        upstream orderbook during the ``update_orderbook`` function in the init
        of the algorithm.

        This function triggers the Notification message of the executed order
        and places a new order.
        """
        LOG.info("Handling executed order: %s", closed_order.txid)

        self._event_bus.publish(
            "notification",
            data={
                "message": str(
                    f"✅ {self._rest_api.rest_symbol}: {closed_order.side[0].upper()}{closed_order.side[1:]} "
                    "order executed"
                    f"\n ├ Price » {closed_order.price} {self._config.quote_currency}"
                    f"\n ├ Size » {closed_order.vol_exec} {self._config.base_currency}"
                    f"\n └ Size in {self._config.quote_currency} » "
                    f"{float(closed_order.price) * float(closed_order.vol_exec)}",
                ),
            },
        )
        # ======================================================================
        # If a buy order was filled, the sell order needs to be placed.
        if closed_order.side == self._exchange_domain.BUY:
            self._handle_arbitrage(
                side=self._exchange_domain.SELL,
                order_price=self._get_sell_order_price(
                    last_price=closed_order.price,
                    buy_txid=closed_order.txid,
                ),
                txid_to_delete=closed_order.txid,
            )

        # ======================================================================
        # If a sell order was filled, we may need to place a new buy order.
        elif closed_order.side == self._exchange_domain.SELL:
            # A new buy order will only be placed if there is another sell
            # order, because if the last sell order was filled, the price is so
            # high, that all buy orders will be canceled anyway and new buy
            # orders will be placed in ``check_price_range`` during shift-up.
            if (
                self._orderbook_table.count(
                    filters={"side": self._exchange_domain.SELL},
                    exclude={"txid": closed_order.txid},
                )
                != 0
            ):
                self._handle_arbitrage(
                    side=self._exchange_domain.BUY,
                    order_price=self._get_buy_order_price(
                        last_price=closed_order.price,
                    ),
                    txid_to_delete=closed_order.txid,
                )
            else:
                self._orderbook_table.remove(filters={"txid": closed_order.txid})

    def __sync_order_book(self: Self) -> None:
        """
        This function only gets triggered once during the setup of the
        algorithm.

        It checks:

        - if the orderbook is up to date, remove filled, closed, and
          canceled orders.
        - if the local orderbook for changes - comparison with upstream
          orderbook
        - and will place new orders if filled.
        """
        LOG.info("- Syncing the orderbook with upstream...")

        # ======================================================================
        # Only track orders that belong to this instance.
        ##
        open_orders: list[OrderInfoSchema] = self.__update_orderbook_get_open_orders()
        open_txids: set[str] = {order.txid for order in open_orders}

        # ======================================================================
        # Orders of the upstream which are not yet tracked in the local
        # orderbook will now be added to the local orderbook.
        ##
        local_txids: set[str] = {
            order["txid"] for order in self._orderbook_table.get_orders()
        }
        for order in open_orders:
            if order.txid not in local_txids:
                LOG.info(
                    "  - Adding upstream order to local orderbook: %s",
                    order.txid,
                )
                self._orderbook_table.add(order)

        # ======================================================================
        # Check all orders of the local orderbook against those from upstream.
        # If they got filled -> place new orders.
        # If canceled -> remove from local orderbook.
        ##
        for order in self._orderbook_table.get_orders():
            if order["txid"] not in open_txids:
                closed_order: OrderInfoSchema = self._rest_api.get_order_with_retry(
                    txid=order["txid"],
                )
                # ==============================================================
                # Order was filled
                if closed_order.status == self._exchange_domain.CLOSED:
                    self.__update_order_book_handle_closed_order(
                        closed_order=closed_order,
                    )

                # ==============================================================
                # Order was closed
                elif closed_order.status in {
                    self._exchange_domain.CANCELED,
                    self._exchange_domain.EXPIRED,
                }:
                    self._orderbook_table.remove(filters={"txid": order["txid"]})

                else:
                    # pending || open order - still active
                    ##
                    continue

        # There are no more filled/closed and cancelled orders in the local
        # orderbook and all upstream orders are tracked locally.
        LOG.info("- Orderbook initialized!")

    def __check_configuration_changes(self: Self) -> None:
        """
        Checking if the database content match with the setup parameters of this
        instance. A change may happen in case the bot configuration is updated.

        Checking if the order size or the interval have changed, requiring
        all open buy orders to be cancelled.
        """
        LOG.info("- Checking configuration changes...")
        cancel_all_orders = False

        if (
            self._config.amount_per_grid
            != self._configuration_table.get()["amount_per_grid"]
        ):
            LOG.info(" - Amount per grid changed => cancel open buy orders soon...")
            self._configuration_table.update(
                {"amount_per_grid": self._config.amount_per_grid},
            )
            cancel_all_orders = True

        if self._config.interval != self._configuration_table.get()["interval"]:
            LOG.info(" - Interval changed => cancel open buy orders soon...")
            self._configuration_table.update({"interval": self._config.interval})
            cancel_all_orders = True

        # Check if trailing stop profit configuration changed
        current_tsp = self._configuration_table.get().get("trailing_stop_profit")
        if self._config.trailing_stop_profit != current_tsp:
            LOG.info(" - Trailing stop profit changed => updating configuration...")
            self._configuration_table.update(
                {"trailing_stop_profit": self._config.trailing_stop_profit},
            )

        if cancel_all_orders:
            self.__cancel_all_open_buy_orders()

        LOG.info("- Configuration checked and up-to-date!")

    # ==========================================================================

    def __check_price_range(self: Self) -> None:
        """
        Checks if the orders prices match the conditions of the bot respecting
        the current price.

        If the price (``self.ticker``) raises to high, the open buy orders
        will be canceled and new buy orders below the price respecting the
        interval will be placed.
        """
        if self._config.dry_run:
            LOG.debug("Dry run, not checking price range.")
            return

        LOG.debug("Check conditions for upgrading the grid...")

        if self.__check_pending_txids():
            LOG.debug("Not checking price range because of pending txids.")
            return

        # Remove orders that are next to each other
        self.__check_near_buy_orders()

        # Ensure $n$ open buy orders
        self.__check_n_open_buy_orders()

        # Return if some newly placed order is still pending and not in the
        # orderbook.
        if self._pending_txids_table.count() != 0:
            return

        # Check if there are more than $n$ buy orders and cancel the lowest
        self.__check_lowest_cancel_of_more_than_n_buy_orders()

        # Check the price range and shift the orders up if required
        if self.__shift_buy_orders_up():
            return

        # Place extra sell order (only for SWING strategy)
        self._check_extra_sell_order()

        if self._config.trailing_stop_profit:
            # Handle TSP
            self.__process_future_orders()
            self.__associate_sell_orders_with_tsp()
            self.__check_tsp()

    def __process_future_orders(self: Self) -> None:
        """
        Process pending future orders (mainly from TSP shifts).

        This creates actual sell orders from the future_orders table entries.
        """
        if self._config.dry_run:
            LOG.debug("Dry run, not processing future orders.")
            return

        for future_order in self._future_orders_table.get():
            LOG.info("Processing future order at price %s", future_order["price"])
            self._new_sell_order(order_price=future_order["price"])
            self._future_orders_table.remove_by_price(price=future_order["price"])

    # ==========================================================================
    def __add_missed_sell_orders(self: Self) -> None:
        """
        This functions can create sell orders in case there is at least one
        executed buy order that is missing its sell order.

        Missed sell orders came into place when a buy was executed and placing
        the sell failed. An entry to the missed sell order id table is added
        right before placing a sell order.
        """
        LOG.info("- Create sell orders based on unsold buy orders...")
        for entry in self._unsold_buy_order_txids_table.get():
            LOG.info("  - %s", entry)
            self._handle_arbitrage(
                side=self._exchange_domain.SELL,
                order_price=entry["price"],
                txid_to_delete=entry["txid"],
            )

    def __check_near_buy_orders(self: Self) -> None:
        """
        Cancel buy orders that are next to each other. Only the lowest buy order
        will survive. This is to avoid that the bot buys at the same price
        multiple times.

        Other functions handle the eventual cancellation of a very low buy order
        to avoid falling out of the price range.
        """
        LOG.debug("Checking if distance between buy orders is too low...")

        if len(buy_prices := list(self._get_current_buy_prices())) == 0:
            return

        buy_prices.sort(reverse=True)
        for i, price in enumerate(buy_prices[1:]):
            if (
                price == buy_prices[i]
                or (buy_prices[i] / price) - 1 < self._config.interval / 2
            ):
                for order in self._orderbook_table.get_orders(
                    filters={"side": self._exchange_domain.BUY},
                ):
                    if order["price"] == buy_prices[i]:
                        self._handle_cancel_order(txid=order["txid"])
                        break

    def __check_n_open_buy_orders(self: Self) -> None:
        """
        Ensures that there are n open buy orders and will place orders until n.
        """
        LOG.debug(
            "Checking if there are %d open buy orders...",
            self._config.n_open_buy_orders,
        )
        can_place_buy_order: bool = True
        buy_prices: list[float] = list(self._get_current_buy_prices())
        while (
            (
                n_active_buy_orders := self._orderbook_table.count(
                    filters={"side": self._exchange_domain.BUY},
                )
            )
            < self._config.n_open_buy_orders
            and can_place_buy_order
            and self._pending_txids_table.count() == 0
            and not self._max_investment_reached
        ):
            fetched_balances = self._rest_api.get_pair_balance()
            if fetched_balances.quote_available > self._amount_per_grid_plus_fee:
                order_price: float = self._get_buy_order_price(
                    last_price=(
                        self._ticker if n_active_buy_orders == 0 else min(buy_prices)
                    ),
                )

                self._handle_arbitrage(
                    side=self._exchange_domain.BUY,
                    order_price=order_price,
                )
                buy_prices = list(self._get_current_buy_prices())
                LOG.debug("Length of active buy orders: %s", n_active_buy_orders + 1)
            else:
                LOG.warning("Not enough quote currency available to place buy order!")
                can_place_buy_order = False

    def __check_lowest_cancel_of_more_than_n_buy_orders(self: Self) -> None:
        """
        Cancel the lowest buy order if new higher buy was placed because of an
        executed sell order.
        """
        LOG.debug("Checking if the lowest buy order needs to be canceled...")

        if (
            n_to_cancel := (
                self._orderbook_table.count(filters={"side": self._exchange_domain.BUY})
                - self._config.n_open_buy_orders
            )
        ) > 0:
            for order in self._orderbook_table.get_orders(
                filters={"side": self._exchange_domain.BUY},
                order_by=("price", "asc"),
                limit=n_to_cancel,
            ):
                self._handle_cancel_order(txid=order["txid"])

    def __cancel_all_open_buy_orders(self: Self) -> None:
        """
        Cancels all open buy orders and removes them from the orderbook.
        """
        LOG.info("Cancelling all open buy orders...")
        for order in self._rest_api.get_open_orders(userref=self._config.userref):
            if (
                order.side == self._exchange_domain.BUY
                and order.pair == self._rest_api.rest_altname
            ):
                self._handle_cancel_order(txid=order.txid)
                sleep(0.2)  # Avoid rate limiting

        # FIXME: Check if not needed, handle_cancel_order should take care of it
        # self._orderbook_table.remove(filters={"side": self._exchange_domain.BUY})

    def __shift_buy_orders_up(self: Self) -> bool:
        """
        Checks if the buy order prices are not to low. If there are too low,
        they get canceled and the ``check_price_range`` function is triggered
        again to place new buy orders.

        Returns ``True`` if the orders get canceled and the
        ``check_price_range`` functions stops.
        """
        LOG.debug("Checking if buy orders need to be shifted up...")

        if (
            max_buy_order := self._orderbook_table.get_orders(
                filters={"side": self._exchange_domain.BUY},
                order_by=("price", "desc"),
                limit=1,
            ).first()  # type: ignore[no-untyped-call]
        ) and (
            self._ticker
            > max_buy_order["price"]
            * (1 + self._config.interval)
            * (1 + self._config.interval)
            * 1.001
        ):
            self.__cancel_all_open_buy_orders()
            self.__check_price_range()
            return True

        return False

    def _handle_arbitrage(
        self: Self,
        side: str,
        order_price: float,
        txid_to_delete: str | None = None,
    ) -> None:
        """
        Handles the arbitrage between buy and sell orders.

        The existence of this function is mainly justified due to the sleep
        statement at the end.
        """
        LOG.debug(
            "Handle arbitrage for %s order with order price: %s and"
            " txid_to_delete: %s",
            side,
            order_price,
            txid_to_delete,
        )

        if self._config.dry_run:
            LOG.info("Dry run, not placing %s order.", side)
            return

        if side == self._exchange_domain.BUY:
            self.new_buy_order(order_price=order_price, txid_to_delete=txid_to_delete)
        elif side == self._exchange_domain.SELL:
            self._new_sell_order(order_price=order_price, txid_to_delete=txid_to_delete)
        else:
            self._state_machine.transition_to(States.ERROR)
            raise BotStateError(
                f"Unknown side '{side}' for arbitrage handling in {self._rest_api.rest_symbol}!",
            )

        # Wait a bit to avoid rate limiting.
        sleep(0.2)

    def new_buy_order(
        self: Self,
        order_price: float,
        txid_to_delete: str | None = None,
    ) -> None:
        """Places a new buy order."""
        if self._config.dry_run:
            LOG.info("Dry run, not placing buy order.")
            return

        if txid_to_delete is not None:
            self._orderbook_table.remove(filters={"txid": txid_to_delete})

        if (
            self._orderbook_table.count(filters={"side": self._exchange_domain.BUY})
            >= self._config.n_open_buy_orders
        ):
            # Don't place new buy orders if there are already enough
            return

        # Check if algorithm reached the max_investment value
        if self._max_investment_reached:
            return

        # Compute the target price for the upcoming buy order.
        order_price = float(
            self._rest_api.truncate(
                amount=order_price,
                amount_type="price",
            ),
        )

        # Compute the target volume for the upcoming buy order.
        # NOTE: The fee is respected while placing the sell order
        volume = float(
            self._rest_api.truncate(
                amount=Decimal(self._config.amount_per_grid) / Decimal(order_price),
                amount_type="volume",
            ),
        )

        # ======================================================================
        # Check if there is enough quote balance available to place a buy order.
        current_balances = self._rest_api.get_pair_balance()
        if current_balances.quote_available > self._amount_per_grid_plus_fee:
            LOG.info(
                "Placing order to buy %s %s @ %s %s.",
                volume,
                self._config.base_currency,
                order_price,
                self._config.quote_currency,
            )

            # Place a new buy order, append txid to pending list and delete
            # corresponding sell order from local orderbook.
            placed_order = self._rest_api.create_order(
                ordertype="limit",
                side=self._exchange_domain.BUY,
                volume=volume,
                price=order_price,
                userref=self._config.userref,
                validate=self._config.dry_run,
                oflags="post",  # post-only buy orders
            )

            self._pending_txids_table.add(placed_order.txid)
            self._assign_order_by_txid(placed_order.txid)
            return

        # ======================================================================
        # Not enough available funds to place a buy order.
        message = f"⚠️ {self._rest_api.rest_symbol}\n"
        message += f"├ Not enough {self._config.quote_currency}\n"
        message += f"├ to buy {volume} {self._config.base_currency}\n"
        message += f"└ for {order_price} {self._config.quote_currency}"
        self._event_bus.publish("notification", data={"message": message})
        LOG.warning("Current balances: %s", current_balances)

    def handle_filled_order_event(self: Self, txid: str) -> None:
        """
        Gets triggered by a filled order event from the ``on_message`` function.

        It fetches the filled order info (using some tries).

        If there is the KeyError which happens due to Krakens shitty, then wait
        for one second and this function will call it self again and return.
        """
        LOG.debug("Handling a new filled order event for txid: %s", txid)

        # ======================================================================
        # Fetch the order details for the given txid.
        ##
        order_details: OrderInfoSchema = self._rest_api.get_order_with_retry(txid=txid)

        # ======================================================================
        # Check if the order belongs to this bot and return if not
        ##
        if (
            order_details.pair != self._rest_api.rest_altname
            or order_details.userref != self._config.userref
        ):
            LOG.debug(
                "Filled order %s was not from this bot or pair.",
                txid,
            )
            return

        # ======================================================================
        # Sometimes the order is not closed yet, so retry fetching the order.
        ##
        tries = 1
        while order_details.status != self._exchange_domain.CLOSED and tries <= 3:
            order_details = self._rest_api.get_order_with_retry(
                txid=txid,
                exit_on_fail=False,
            )
            LOG.warning(
                "Order '%s' is not closed! Retry %d/3 in %d seconds...",
                txid,
                tries,
                (wait_time := 2 + tries),
            )
            sleep(wait_time)
            tries += 1

        if order_details.status != self._exchange_domain.CLOSED:
            LOG.warning(
                "Can not handle filled order, since the fetched order is not"
                " closed in upstream!"
                " This may happen due to websocket API being faster"
                " than the REST backend. Retrying in a few seconds...",
            )
            self.handle_filled_order_event(txid=txid)
            return

        # ======================================================================
        if self._config.dry_run:
            LOG.info("Dry run, not handling filled order event.")
            return

        # ======================================================================
        # Notify about the executed order
        ##
        self._event_bus.publish(
            "notification",
            data={
                "message": str(
                    f"✅ {self._rest_api.rest_symbol}: "
                    f"{order_details.side[0].upper()}{order_details.side[1:]} "
                    "order executed"
                    f"\n ├ Price » {order_details.price} {self._config.quote_currency}"
                    f"\n ├ Size » {order_details.vol_exec} {self._config.base_currency}"
                    f"\n └ Size in {self._config.quote_currency} » "
                    f"{round(order_details.price * order_details.vol_exec, self._cost_decimals)}",
                ),
            },
        )

        # ======================================================================
        # Create a sell order for the executed buy order.
        ##
        if order_details.side == self._exchange_domain.BUY:
            sell_price = self._get_sell_order_price(last_price=order_details.price)

            self._handle_arbitrage(
                side=self._exchange_domain.SELL,
                order_price=sell_price,
                txid_to_delete=txid,
            )

            # Initialize TSP state if TSP is enabled
            if self._config.trailing_stop_profit:
                self._initialize_tsp_for_new_position(
                    original_buy_txid=txid,
                    buy_price=order_details.price,
                    sell_price=sell_price,
                )

        # ==================================================================
        # Create a buy order for the executed sell order.
        ##
        elif order_details.side == self._exchange_domain.SELL:
            # Clean up TSP state if a sell order was filled
            if self._config.trailing_stop_profit:
                self._cleanup_tsp_state_for_filled_sell_order(txid)

            if (
                self._orderbook_table.count(
                    filters={"side": self._exchange_domain.SELL},
                    exclude={"txid": txid},
                )
                != 0
            ):
                # A new buy order will only be placed if there is another sell
                # order, because if the last sell order was filled, the price is so
                # high, that all buy orders will be canceled anyway and new buy
                # orders will be placed in ``check_price_range`` during shift-up.
                self._handle_arbitrage(
                    side=self._exchange_domain.BUY,
                    order_price=self._get_buy_order_price(
                        last_price=order_details.price,
                    ),
                    txid_to_delete=txid,
                )
            else:
                # Remove filled order from list of all orders
                self._orderbook_table.remove(filters={"txid": txid})

    def _handle_cancel_order(self: Self, txid: str) -> None:
        """
        Cancels an order by txid, removes it from the orderbook, and checks if
        there there was some volume executed which can be sold later in case of
        a buy order.

        NOTE: The orderbook is the "gate keeper" of this function. If the order
              is not present in the local orderbook, nothing will happen.

        For post-only buy orders - if these were cancelled by Kraken, they are
        still in the local orderbook and will be handled just like regular calls
        of the handle_cancel_order of the algorithm.

        For orders that were cancelled by the algorithm, these will cancelled
        via API and removed from the orderbook. The incoming "canceled" message
        by the websocket will be ignored, as the order is already removed from
        the orderbook.
        """
        if self._orderbook_table.count(filters={"txid": txid}) == 0:
            return

        order_details: OrderInfoSchema = self._rest_api.get_order_with_retry(txid=txid)

        if (
            order_details.pair != self._rest_api.rest_altname
            or order_details.userref != self._config.userref
        ):
            LOG.debug(
                "Not handling cancellation for order '%s' - not from this instance.",
                txid,
            )
            return

        if self._config.dry_run:
            LOG.info("DRY RUN: Not cancelling order: %s", txid)
            return

        LOG.info("Cancelling order: '%s'", txid)

        try:
            self._rest_api.cancel_order(txid=txid)
        except UnknownOrderError:
            LOG.info(
                "Order '%s' is already closed. Removing from orderbook...",
                txid,
            )

        self._orderbook_table.remove(filters={"txid": txid})

        # Clean up TSP state if this was a sell order being canceled
        if order_details.side == self._exchange_domain.SELL:
            # Don't remove TSP state here as the order might be replaced
            # TSP state cleanup happens when position is actually closed
            pass

        # Check if the order has some vol_exec to sell
        ##
        if (
            order_details.vol_exec != 0.0
            and order_details.side == self._exchange_domain.BUY
        ):
            LOG.info(
                "Order '%s' is partly filled - saving those funds.",
                txid,
            )
            b = self._configuration_table.get()

            # Add vol_exec to remaining funds
            updates = {
                "vol_of_unfilled_remaining": b["vol_of_unfilled_remaining"]
                + order_details.vol_exec,
            }

            # Set new highest buy price.
            if b["vol_of_unfilled_remaining_max_price"] < order_details.price:
                updates |= {"vol_of_unfilled_remaining_max_price": order_details.price}
            self._configuration_table.update(updates)

            # Sell remaining funds if there is enough to place a sell order.
            # Its not perfect but good enough. (Some funds may still be
            # stuck) - but better than nothing.
            b = self._configuration_table.get()
            if (
                b["vol_of_unfilled_remaining"]
                * b["vol_of_unfilled_remaining_max_price"]
                >= self._config.amount_per_grid
            ):
                LOG.info(
                    "Collected enough funds via partly filled buy orders to"
                    " create a new sell order...",
                )
                self._handle_arbitrage(
                    side=self._exchange_domain.SELL,
                    order_price=self._get_sell_order_price(
                        last_price=b["vol_of_unfilled_remaining_max_price"],
                    ),
                )
                self._configuration_table.update(  # Reset the remaining funds
                    {
                        "vol_of_unfilled_remaining": 0,
                        "vol_of_unfilled_remaining_max_price": 0,
                    },
                )

    def _assign_all_pending_transactions(self: Self) -> None:
        """Assign all pending transactions to the orderbook."""
        LOG.info("- Checking pending transactions...")
        for order in self._pending_txids_table.get():
            self._assign_order_by_txid(txid=order["txid"])

    def _assign_order_by_txid(self: Self, txid: str) -> None:
        """
        Assigns an order by its txid to the orderbook.

        - Option 1: Removes them from the pending txids and appends it to
                    the orderbook
        - Option 2: Updates the info of the order in the orderbook

        There is no need for checking the order status, since after the order
        was added to the orderbook, the algorithm will handle any removals in
        case of closed orders.
        """
        LOG.info("Processing order '%s' ...", txid)
        order_details: OrderInfoSchema = self._rest_api.get_order_with_retry(txid=txid)
        LOG.debug("- Order information: %s", order_details)

        if (
            order_details.pair != self._rest_api.rest_altname
            or order_details.userref != self._config.userref
        ):
            LOG.info("Order '%s' does not belong to this instance.", txid)
            return

        if self._pending_txids_table.count(filters={"txid": order_details.txid}) != 0:
            self._orderbook_table.add(order_details)
            self._pending_txids_table.remove(order_details.txid)
        else:
            self._orderbook_table.update(order_details)
            LOG.info("Updated order '%s' in orderbook.", order_details.txid)

        LOG.info(
            "Current investment: %f / %d %s",
            self._investment,
            self._config.max_investment,
            self._config.quote_currency,
        )

    def _get_current_buy_prices(self: Self) -> Iterable[float]:
        """Returns a list of the prices of open buy orders."""
        LOG.debug("Getting current buy prices...")
        for order in self._orderbook_table.get_orders(
            filters={"side": self._exchange_domain.BUY},
        ):
            yield order["price"]

    def get_value_of_orders(self: Self, orders: Iterable) -> float:
        """Returns the overall invested quote that is invested"""
        LOG.debug("Getting value of open orders...")
        investment = sum(
            float(order["price"]) * float(order["volume"]) for order in orders
        )
        LOG.debug(
            "Value of open orders: %s %s",
            investment,
            self._config.quote_currency,
        )
        return investment

    @property
    def _investment(self: Self) -> float:
        """Returns the current investment based on open orders."""
        return self.get_value_of_orders(orders=self._orderbook_table.get_orders())

    @property
    def _max_investment_reached(self: Self) -> bool:
        """Returns True if the maximum investment is reached."""
        return (
            self._config.max_investment
            <= self._investment + self._amount_per_grid_plus_fee
        ) or (self._config.max_investment <= self._investment)

    def __check_pending_txids(self: Self) -> bool:
        """
        Skip checking the price range, because first all missing orders
        must be assigned. Otherwise this could lead to double trades.

        Returns False if okay and True if ``check_price_range`` must be skipped.
        """
        if self._pending_txids_table.count() != 0:
            LOG.info("check_price_range... skip because pending_txids != 0")
            self._assign_all_pending_transactions()
            return True
        return False

    def send_status_update(self: Self) -> None:
        """Send a message to the Notification channel with the current status."""
        balances = self._rest_api.get_pair_balance()

        message = f"👑 {self._config.name}\n"
        message += f"└ Price » {self._ticker} {self._config.quote_currency}\n\n"

        message += "⚜️ Account\n"
        message += f"├ Total {self._config.base_currency} » {balances.base_balance}\n"
        message += f"├ Total {self._config.quote_currency} » {balances.quote_balance}\n"
        message += (
            f"├ Available {self._config.quote_currency} » {balances.quote_available}\n"
        )
        message += f"├ Available {self._config.base_currency} » {balances.base_available - float(self._configuration_table.get()['vol_of_unfilled_remaining'])}\n"  # noqa: E501
        message += f"├ Unfilled surplus of {self._config.base_currency} » {self._configuration_table.get()['vol_of_unfilled_remaining']}\n"  # noqa: E501
        message += f"├ Wealth » {round(balances.base_balance * self._ticker + balances.quote_balance, self._cost_decimals)} {self._config.quote_currency}\n"  # noqa: E501
        message += f"└ Investment » {round(self._investment, self._cost_decimals)} / {self._config.max_investment} {self._config.quote_currency}\n\n"  # noqa: E501

        message += "💠 Orders\n"
        message += f"├ Amount per Grid » {self._config.amount_per_grid} {self._config.quote_currency}\n"
        message += f"└ Open orders » {self._orderbook_table.count()}\n"

        message += "\n```\n"
        message += f" 🏷️ Price in {self._config.quote_currency}\n"
        max_orders_to_list: int = 5

        next_sells = [
            order["price"]
            for order in self._orderbook_table.get_orders(
                filters={"side": self._exchange_domain.SELL},
                order_by=("price", "ASC"),
                limit=max_orders_to_list,
            )
        ]
        next_sells.reverse()
        next_buys = [
            order["price"]
            for order in self._orderbook_table.get_orders(
                filters={"side": self._exchange_domain.BUY},
                order_by=("price", "DESC"),
                limit=max_orders_to_list,
            )
        ]
        n_buys = len(next_buys)

        if (n_sells := len(next_sells)) == 0:
            if n_buys == 0:
                # This only happens if there are not enough funds to place a buy
                # order or if the bot is in dry run mode.
                message += f"└────> {self._ticker}\n"
            else:
                message += f"└───┬> {self._ticker}\n"
        else:
            for index, sell_price in enumerate(next_sells):
                change = (sell_price / self._ticker - 1) * 100
                if index == 0:
                    message += f" │  ┌[ {sell_price} (+{change:.2f}%)\n"
                elif index <= n_sells - 1 and index != max_orders_to_list:
                    message += f" │  ├[ {sell_price} (+{change:.2f}%)\n"
            message += f" └──┼> {self._ticker}\n"

        if n_buys != 0:
            for index, buy_price in enumerate(next_buys):
                change = (buy_price / self._ticker - 1) * 100
                if index < n_buys - 1 and index != max_orders_to_list:
                    message += f"    ├[ {buy_price} ({change:.2f}%)\n"
                else:
                    message += f"    └[ {buy_price} ({change:.2f}%)"
        message += "\n```"

        self._event_bus.publish("notification", data={"message": message})
        self._last_status_update = datetime.now()

    # ==========================================================================

    def _get_buy_order_price(self: Self, last_price: float) -> float:
        """Returns the order price for the next buy order."""
        factor = 100 / (100 + 100 * self._config.interval)
        if (order_price := float(last_price) * factor) > self._ticker:
            order_price = self._ticker * factor
        return order_price

    def _get_sell_order_price(
        self: Self,
        last_price: float,
        buy_txid: str | None = None,  # Keep for API compatibility but not used
    ) -> float:
        """
        Returns the order price. Also assigns a new highest buy price to
        configuration if there was a new highest buy.

        If TSP is enabled, sets initial sell price higher (interval + 2x TSP).
        """
        LOG.debug("Computing the order price...")

        order_price: float
        price_of_highest_buy = self._configuration_table.get()["price_of_highest_buy"]
        last_price = float(last_price)

        if last_price > price_of_highest_buy:
            self._configuration_table.update({"price_of_highest_buy": last_price})

        # Check if TSP is enabled
        if self._config.trailing_stop_profit:
            # For TSP: Initial sell target is interval + 2×TSP
            factor = 1 + self._config.interval + (2 * self._config.trailing_stop_profit)
            LOG.debug("TSP enabled: using factor %s for initial sell price", factor)
        else:
            # Standard sell price: 1x interval above buy price
            factor = 1 + self._config.interval

        if (order_price := last_price * factor) < self._ticker:
            order_price = self._ticker * factor

        return order_price

    # ==========================================================================

    def _check_extra_sell_order(self: Self) -> None:  # pragma: no cover
        """
        Checks if an extra sell order can be placed. This only applies for the
        SWING strategy.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def _new_sell_order(
        self: Self,
        order_price: float,
        txid_to_delete: str | None = None,
    ) -> None:  # pragma: no cover
        """
        Places a new sell order.

        This method should be implemented by the concrete strategy classes.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    # ==========================================================================
    #  Trailing Stop Profit

    def __check_tsp(self: Self) -> None:
        """Check and manage Trailing Stop Profit for all tracked positions."""
        if (
            not self._config.trailing_stop_profit
            or self._config.dry_run
            or not self._ticker
        ):
            return

        LOG.debug("Checking TSP conditions at price: %s", self._ticker)

        tsp_percentage = self._config.trailing_stop_profit
        interval = self._config.interval

        # Process each sell order and match with TSP state
        for sell_order in self._orderbook_table.get_orders(
            filters={"side": self._exchange_domain.SELL},
        ).all():
            sell_price, sell_txid = sell_order["price"], sell_order["txid"]

            # Try to find existing TSP state for this sell order
            if not (tsp_state := self._tsp_state_table.get_by_sell_txid(sell_txid)):
                # This sell order doesn't have TSP state yet
                # This can happen for:
                # 1. Sell orders from shift-up operations
                # 2. Extra sell orders from SWING strategy
                LOG.debug(
                    "No TSP state found for sell order '%s', skipping TSP check",
                    sell_txid,
                )
                continue

            # Skip if original buy price is higher than the current price
            if (original_buy_price := tsp_state["original_buy_price"]) > self._ticker:
                continue

            original_buy_txid = tsp_state["original_buy_txid"]
            current_stop_price = tsp_state["current_stop_price"]
            tsp_activation_price = original_buy_price * (1 + interval + tsp_percentage)

            # Check if TSP should be activated
            if not tsp_state["tsp_active"] and self._ticker >= tsp_activation_price:
                LOG.info(
                    "Activating TSP for position %s (buy_price=%s) at current price %s",
                    original_buy_txid,
                    original_buy_price,
                    self._ticker,
                )

                # Activate TSP
                self._tsp_state_table.activate_tsp(original_buy_txid, self._ticker)

                # Calculate new sell order price (move it up by TSP amount)
                LOG.info(
                    "Try shifting sell order from %s to %s (TSP activation)",
                    sell_price,
                    new_sell_price := sell_price
                    + (original_buy_price * tsp_percentage),
                )

                # Cancel current sell order
                self._handle_cancel_order(txid=sell_txid)

                # Use future orders to place the new sell order
                self._future_orders_table.add(price=new_sell_price)

                # Update the TSP state to clear the old sell order TXID The new
                # sell order will get associated later in
                # __associate_sell_orders_with_tsp
                self._tsp_state_table.update_sell_order_txid_by_buy_txid(
                    original_buy_txid=original_buy_txid,
                    new_sell_txid=None,
                )

                self._event_bus.publish(
                    "notification",
                    data={
                        "message": "↗️ Shifting up sell order from"
                        f" {sell_price} {self._config.quote_currency}"
                        f" to {new_sell_price} {self._config.quote_currency}"
                        f" due to activated TSP at {current_stop_price} {self._config.quote_currency}",
                    },
                )

                continue

            # For active TSP positions, check for trailing stop updates and triggers
            if tsp_state["tsp_active"]:
                # Update trailing stop if price has moved higher than threshold
                if self._ticker >= sell_price - (original_buy_price * tsp_percentage):
                    self._tsp_state_table.update_trailing_stop(
                        original_buy_txid=original_buy_txid,
                        current_price=self._ticker,
                    )
                    LOG.debug(
                        "Updated trailing stop for position '%s' to new level",
                        original_buy_txid,
                    )

                    # Shift the leading sell order further up
                    new_sell_price = sell_price + (original_buy_price * tsp_percentage)
                    self._handle_cancel_order(txid=sell_txid)
                    self._future_orders_table.add(price=new_sell_price)

                    # Update the TSP state to clear the old sell order TXID
                    self._tsp_state_table.update_sell_order_txid_by_buy_txid(
                        original_buy_txid=original_buy_txid,
                        new_sell_txid=None,
                    )
                    LOG.debug("Shifted leading sell order up to %s", new_sell_price)
                    self._event_bus.publish(
                        "notification",
                        data={
                            "message": "↗️ Shifting up sell order from"
                            f" {sell_price} {self._config.quote_currency}"
                            f" to {new_sell_price} {self._config.quote_currency}"
                            f" new trailing stop at {self._ticker * (1 - tsp_percentage)}"
                            f" {self._config.quote_currency}",
                        },
                    )

                # Check if trailing stop should trigger
                elif self._ticker <= current_stop_price:
                    LOG.info(
                        "TSP triggered! Selling position '%s' at trailing stop level %s",
                        original_buy_txid,
                        current_stop_price,
                    )
                    self._event_bus.publish(
                        "notification",
                        data={
                            "message": f"⚠️ Trailing stop profit triggered at {current_stop_price}",
                        },
                    )

                    # Cancel the leading sell order
                    self._handle_cancel_order(txid=sell_txid)

                    # Create sell order at the trailing stop level
                    # Ensure the sale is profitable (above minimum)
                    min_profitable_price = original_buy_price * (
                        1 + interval + 2 * self._config.fee
                    )
                    actual_sell_price = max(self._ticker, min_profitable_price)

                    # Place immediate sell order
                    self._place_tsp_sell_order(original_buy_txid, actual_sell_price)

                    # Clean up TSP state
                    self._tsp_state_table.remove_by_buy_txid(original_buy_txid)

                    LOG.info(
                        "TSP sell executed at %s for position %s",
                        actual_sell_price,
                        original_buy_txid,
                    )

    def _place_tsp_sell_order(
        self: Self,
        original_buy_txid: str,
        sell_price: float,
    ) -> None:
        """
        Place a TSP-triggered sell order.

        This uses the existing arbitrage mechanism to place an immediate sell order.
        """
        LOG.info(
            "Placing TSP sell order at price %s for position %s",
            sell_price,
            original_buy_txid,
        )

        # Use the standard arbitrage mechanism to place the sell order
        # This will call _new_sell_order which is implemented by subclasses
        self._handle_arbitrage(side=self._exchange_domain.SELL, order_price=sell_price)

    def _cleanup_tsp_state_for_filled_sell_order(self: Self, sell_txid: str) -> None:
        """
        Clean up TSP state when a sell order is filled.

        This is crucial to prevent orphaned TSP states.
        """
        LOG.debug("Cleaning up TSP state for filled sell order: %s", sell_txid)

        # Find and remove TSP state associated with this sell order
        if tsp_state := self._tsp_state_table.get_by_sell_txid(sell_txid):
            LOG.info(
                "Removing TSP state for position %s after sell order %s filled",
                original_buy_txid := tsp_state["original_buy_txid"],
                sell_txid,
            )
            self._tsp_state_table.remove_by_buy_txid(original_buy_txid)
        else:
            LOG.debug("No TSP state found for sell order %s", sell_txid)

    def _initialize_tsp_for_new_position(
        self: Self,
        original_buy_txid: str,
        buy_price: float,
        sell_price: float,
    ) -> None:
        """
        Initialize TSP state when a new position is created (buy order filled +
        sell order placed).

        This sets up TSP tracking from the beginning of the position lifecycle.
        We store the buy order information and will link it to the sell order
        later when we process the TSP check loop.
        """
        LOG.debug(
            "Initializing TSP for position: buy_txid=%s, buy_price=%s, sell_price=%s",
            original_buy_txid,
            buy_price,
            sell_price,
        )

        interval = self._config.interval
        initial_stop_price = buy_price * (1 + interval)  # Minimum profit level

        # Store the buy information with a placeholder for sell TXID
        # The sell TXID will be updated in the next TSP check cycle
        self._tsp_state_table.add(
            original_buy_txid=original_buy_txid,
            original_buy_price=buy_price,
            initial_stop_price=initial_stop_price,
            sell_order_txid=None,  # Will be updated in __associate_sell_orders_with_tsp()
        )

    def __associate_sell_orders_with_tsp(self: Self) -> None:
        """
        Associate new sell orders with their corresponding TSP states.

        These sell orders are either placed because of an executed buy order and
        or a TSP entry of which the sell order is cleared due to shifting up.

        This solves the timing issue where TSP state is created before the sell
        order TXID is available.
        """
        # Get TSP states that don't have sell orders associated yet
        if not (
            unlinked_states := [
                state
                for state in self._tsp_state_table.get_all_active()
                if state["current_sell_order_txid"] is None
            ]
        ):
            return

        sell_orders = self._orderbook_table.get_orders(
            filters={"side": self._exchange_domain.SELL},
        ).all()

        for tsp_state in unlinked_states:
            # Find sell order that matches this position. We calculate what the
            # sell price should be based on original buy price.
            expected_sell_price = tsp_state["original_buy_price"] * (
                1 + self._config.interval + 2 * self._config.trailing_stop_profit
            )

            # Find closest matching sell order (within tolerance)
            tolerance = 0.01  # 1% tolerance for price matching
            matching_sell_order = None

            for sell_order in sell_orders:
                price_diff = (
                    abs(sell_order["price"] - expected_sell_price) / expected_sell_price
                )
                if price_diff <= tolerance:
                    # Check if this sell order is already associated with
                    # another TSP state.
                    existing_tsp = self._tsp_state_table.get_by_sell_txid(
                        sell_order["txid"],
                    )
                    if not existing_tsp:
                        matching_sell_order = sell_order
                        break

            if matching_sell_order:
                LOG.debug(
                    "Associating sell order %s with TSP state for buy %s",
                    matching_sell_order["txid"],
                    tsp_state["original_buy_txid"],
                )
                self._tsp_state_table.update_sell_order_txid_by_buy_txid(
                    original_buy_txid=tsp_state["original_buy_txid"],
                    new_sell_txid=matching_sell_order["txid"],
                )
            else:
                LOG.warning(
                    "Could not find matching sell order for TSP state with buy TXID %s (expected price: %s)",
                    tsp_state["original_buy_txid"],
                    expected_sell_price,
                )
