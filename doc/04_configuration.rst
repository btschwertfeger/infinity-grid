.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2025 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

.. _configuration-section:

Configuration
=============

The algorithm is designed to be highly configurable and can be adjusted to your
needs. The following configuration variables can be either set as command-line
arguments or via environment variables. They are mapped to the corresponding
command-line arguments internally.

🛠️ Strategy configuration
-------------------------

In order to run the available strategies efficiently, one need to know the
configuration of those. Even though these strategies follow different
approaches, they share the same fundamental concept and configuration
properties. In the following, the most important of them are explained in order
to guide you through the configuration process.

🔭 Choosing the right strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choosing the right strategy is crucial for success. The strategies differ in
their approach and are designed for different market conditions (see
:ref:`Strategies <strategies-section>`). Make sure to understand all of them
before choosing the right one for your needs.

💵 Choosing the right base and quote currency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The base and quote currency should be chosen wisely. The base currency is the
currency you want to trade with, and the quote currency is the currency you want
to trade against. The base and quote currencies should be chosen based on your
trading preferences and the liquidity of the market. Currency pairs with high
volatility can lead to higher profits but also to higher risks.

📈 Choosing the optimal interval
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The interval defines the percentage difference between the buy and sell orders.
The interval should be chosen based on the volatility of the market. A higher
interval, e.g., 4 % leads to higher profits when selling an asset,
and reduces the amount of orders in a moderate volatile market. A lower
interval, e.g., 2 % leads to a higher amount of orders and a lower profit
margin but might be more profitable in markets that oscillate in a smaller
interval.

Consequently the interval should be chosen based on the volatility of the market
and the risk you are willing to take. A higher interval is less risky but since
prices not always reach the placed buy or sell orders (... since markets don't
go exactly e.g., 4 % up and down), it can lead to less executed orders resulting
in lower profits. In contrast to that, a lower interval is more risky, as prices
can rise and fall rapidly but can lead to a higher profits if the market's
volatility matches the grid interval.

.. NOTE:: The value passed to the interval is a percentage value. For example,
          an interval of 4 % means that the buy and sell orders are placed 4 %
          apart from each other. In this case, you have to pass a value of
          ``0.04`` to ``--interval`` or ``INFINITY_GRID_RUN_INTERVAL``.

⚖️ Choosing the optimal amount per grid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The amount per grid defines the amount of the quote currency to use per grid
interval. It should be chosen based on the amount of the quote currency you want
to invest in the market. For example if you want to invest 100 USD per grid
interval (i.e. per trade), the amount per grid should be set to 100. Combining
this amount with an interval of 4 % would result in a profit of about 4 USD per
trade (excluding fees) depending on the strategy used.

When choosing the amount per grid, make sure to consider the amount of the quote
currency in our account, since depending on the number of concurrent open buy
orders, the amount per grid should be balanced. For example, if you have 5 open
buy orders with an amount per grid of 100 USD, you should have at least 500 USD
in your account to cover all open buy orders.

Another aspect to consider is the minimal order sizes of the quote currency that
can be traded on the exchange. Make sure to set the amount per grid higher than
the minimal amount to avoid errors. For further information, check the
exchange's minimum order size for trading documentation.

📊 Choosing the optimal amount of concurrent open buy orders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of concurrent open buy orders defines the number of buy orders that
are open at the same time. This number should be chosen based on the volatility
of the market and the risk you are willing to take. A higher number of open buy
orders secures a rapid price drop of almost 10 % that can be caught immediately,
in case the interval is set to 2 % and number of open buy orders is 5.

As mentioned before, the number of open buy orders should be balanced with the
amount per grid. For example, if you have 5 open buy orders with an amount per
grid of 100 USD, you should have at least 500 USD in your account to cover all
open buy orders.

🏷️ Setting a custom fee
~~~~~~~~~~~~~~~~~~~~~~~

Lastly, exchanges charge fees. The fee is usually a percentage of the traded
amount. If the fee is not set during program start, the highest taker fee for
that currency pair is assumed which doesn't mean that the highest fee is paid.
It is used internally to calculate order sizes, prices, and ensures that profits
are calculated correctly.

Setting a custom fee via the ``--fee`` or ``INFINITY_GRID_RUN_FEE`` option
enables, depending on the strategy, a more accurate profit calculation. For the
average user, this is not necessary. For more information about the fees, check
the fee schedule of the respective exchange.

.. NOTE:: The fee is always paid in the quote currency.

🛡️ Risk management
~~~~~~~~~~~~~~~~~~

Risk management is crucial for successful trading. The algorithm provides
several options to manage the risk. The most important ones are the amount per
grid, the interval, the number of concurrent open buy orders, and the maximum
investment.

Especially the maximum investment is important to prevent the algorithm from
investing more than you are willing to lose. The maximum investment defines the
maximum amount of the quote currency that the algorithm will use for trading.
Setting the maximum investment is recommended and can be done via the
``--max-investment`` or ``INFINITY_GRID_RUN_MAX_INVESTMENT`` option.

The amount per grid, the interval, and the number of concurrent open buy orders
should be chosen based on the maximum investment. In order to demonstrate this,
lets use and example:

Scenario: Trading BTC/USD

- Starting price: 100,000.00 USD per BTC
- Interval: 4.0% (i.e. ``0.04``)
- Amount per grid: 100.00
- Maximum investment: 1,000.00
- Current balance in the account: 5,000.00 USD

You will have the following grid levels for buy, based on the interval and the
starting price, and ensuring to even catch a drawdown of about 34%:

- Grid 1: 96,000.00 USD (-4.00%)
- Grid 2: 92,160.00 USD (-7.84%)
- Grid 3: 88,473.60 USD (-11.53%)
- Grid 4: 84,934.66 USD (-15.07%)
- Grid 5: 81,537.27 USD (-18.46%)
- Grid 6: 78,275.78 USD (-21.72%)
- Grid 7: 75,144.75 USD (-24.86%)
- Grid 8: 72,138.96 USD (-27.86%)
- Grid 9: 69,253.40 USD (-30.75%)
- Grid 10: 66,483.26 USD (-33.52%)

Note that since the maximum investment is set, the algorithm will stop placing
further buy orders if 1,000 USD are already invested with this instance. If a
buy order was executed, depending on the strategy, a sell order will be placed
at 4% higher than the buy order.

.. NOTE:: The grid levels may also not be exactly the same as shown, they are
          just for demonstration purposes. In a real life scenario, the grid
          levels are calculated based on the interval and current market prices,
          can be shifted up or down based on the market's volatility.

⌨️ Command-line Interface
-------------------------

`infinity-grid`_ provides a command-line interface (CLI) to configure and
run the trading algorithm. The CLI is based on the `Click
<https://click.palletsprojects.com>`_ library and provides a set of commands to
interact with the algorithm.


.. click:: infinity_grid.core.cli:cli
   :prog: infinity-grid
   :nested: full

🏕️ Environment Variables
------------------------

Since `infinity-grid`_ is designed to be run in containerized
environments, the configuration can also be done via environment variables. The
naming pattern follows the convention of the command-line arguments respecting
the ``INFINITY_GRID_`` prefix and `Click's
<https://click.palletsprojects.com/en/stable/options/#values-from-environment-variables>`_
naming convention.

.. list-table:: Configuration Variables
    :header-rows: 1

    * - Variable
      - Type
      - Description
    * - ``INFINITY_GRID_API_PUBLIC_KEY``
      - ``str``
      - The API public key provided by the exchange.
    * - ``INFINITY_GRID_API_SECRET_KEY``
      - ``str``
      - The API secret key provided by the exchange.
    * - ``INFINITY_GRID_RUN_EXCHANGE``
      - ``str``
      - The exchange to trade on.
    * - ``INFINITY_GRID_RUN_NAME``
      - ``str``
      - The name of the instance. Can be any name that is used to differentiate
        between instances of the infinity-grid.
    * - ``INFINITY_GRID_RUN_USERREF``
      - ``int``
      - A reference number to identify the algorithm's orders. This can be a
        timestamp or any integer number.
        **Use different userref's for different instances!**
    * - ``INFINITY_GRID_BOT_VERBOSE``
      - ``int`` / (``-v``, ``-vv``)
      - Enable verbose logging.
    * - ``INFINITY_GRID_RUN_BASE_CURRENCY``
      - ``str``
      - The base currency e.g., ``BTC`` or ``ETH``.
    * - ``INFINITY_GRID_RUN_QUOTE_CURRENCY``
      - ``str``
      - The quote currency e.g., ``USD`` or ``EUR``.
    * - ``INFINITY_GRID_RUN_AMOUNT_PER_GRID``
      - ``float``
      - The quote amount to use per grid interval e.g., ``100`` (USD) per trade.
    * - ``INFINITY_GRID_RUN_INTERVAL``
      - ``float``
      - The interval between orders e.g., ``0.04`` to have 4 % intervals.
    * - ``INFINITY_GRID_RUN_N_OPEN_BUY_ORDERS``
      - ``int``
      - The number of concurrent open buy orders e.g., ``5``. The number of
        always open buy positions specifies how many buy positions should be
        open at the same time. If the interval is defined to 2%, a number of 5
        open buy positions ensures that a rapid price drop of almost 10% that
        can be caught immediately.
    * - ``INFINITY_GRID_RUN_MAX_INVESTMENT``
      - ``str``
      - The maximum investment, e.g. ``1000`` USD that the algorithm will
        manage.
    * - ``INFINITY_GRID_RUN_FEE``
      - ``float``
      - A custom fee percentage, e.g. ``0.0026`` for 0.26 % fee.
    * - ``INFINITY_GRID_RUN_STRATEGY``
      - ``str``
      - The trading strategy, e.g., ``GridHODL``, ``GridSell``, ``SWING``, or ``cDCA``
    * - ``INFINITY_GRID_DRY_RUN``
      - ``bool``
      - Enable dry-run mode (no actual trades).
    * - ``INFINITY_GRID_RUN_SKIP_PRICE_TIMEOUT``
      - ``bool``
      - Skip checking if there was a price update in the last 10 minutes. By
        default, the bot will exit if no recent price data is available. This
        might be useful for assets that aren't traded that often.
    * - ``INFINITY_GRID_RUN_TELEGRAM_TOKEN``
      - ``str``
      - The Telegram bot token for notifications.
    * - ``INFINITY_GRID_RUN_TELEGRAM_CHAT_ID``
      - ``str``
      - The Telegram chat ID for notifications.
    * - ``INFINITY_GRID_RUN_TELEGRAM_THREAD_ID``
      - ``str``
      - The Telegram thread ID for notifications.
    * - ``INFINITY_GRID_RUN_DB_USER``
      - ``str``
      - The PostgreSQL database user.
    * - ``INFINITY_GRID_RUN_DB_NAME``
      - ``str``
      - The PostgreSQL database name.
    * - ``INFINITY_GRID_RUN_DB_PASSWORD``
      - ``str``
      - The PostgreSQL database password.
    * - ``INFINITY_GRID_RUN_DB_HOST``
      - ``str``
      - The PostgreSQL database host.
    * - ``INFINITY_GRID_RUN_DB_PORT``
      - ``int``
      - The PostgreSQL database port.
    * - ``INFINITY_GRID_RUN_SQLITE_FILE``
      - ``str``
      - The path to a local SQLite database file, e.g., ``/path/to/sqlite.db``,
        will be created if it does not exist. If a SQLite database is used, the PostgreSQL database configuration is ignored.
    * - ``INFINITY_GRID_RUN_IN_MEMORY``
      - ``bool``
      - Use an in-memory database (similar to ``--sqlite-file=":memory:"``).

.. _database-configuration-section:

🖥 Database configuration
------------------------

The algorithm requires a PostgreSQL or SQLite database to store the current
orderbook, trades, and the algorithm's state. The database configuration can be
set via environment variables or command-line arguments.

PostgreSQL
~~~~~~~~~~

When using the algorithm as proposed in :ref:`Getting Started
<getting-started-docker-compose-section>` via the provided Docker Compose file,
the PostgreSQL database is automatically configured.

The algorithm requires the following environment variables to be set, in order
to connect to the PostgreSQL database:

- ``INFINITY_GRID_RUN_DB_USER``
- ``INFINITY_GRID_RUN_DB_NAME``
- ``INFINITY_GRID_RUN_DB_PASSWORD``
- ``INFINITY_GRID_RUN_DB_HOST``
- ``INFINITY_GRID_RUN_DB_PORT``

SQLite
~~~~~~

When running the algorithm as a pure Python process or as a Docker container
without further PostgreSQL deployment, the algorithm can use a SQLite database
for local storage.

For this purpose, the option ``--sqlite-file`` can be used to specify the path
to the SQLite database file. The SQLite database is created automatically if it
does not exist.

Alternatively, the ``INFINITY_GRID_RUN_SQLITE_FILE`` environment variable can be used
to specify the path to the SQLite database file.

.. NOTE:: Do not use ``:memory:`` for an in-memory database, as this will
          result in data loss when the algorithm is restarted.
