<h1 align="center">Multi-Exchange Infinity Grid Trading Algorithm</h1>

<div align="center">

[![GitHub](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/btschwertfeger/infinity-grid)
[![Generic
badge](https://img.shields.io/badge/python-3.11+-blue.svg)](https://shields.io/)
[![Downloads](https://static.pepy.tech/personalized-badge/infinity-grid?period=total&units=abbreviation&left_color=grey&right_color=orange&left_text=downloads)](https://pepy.tech/project/infinity-grid)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Typing](https://img.shields.io/badge/typing-mypy-informational)](https://mypy-lang.org/)
[![CI/CD](https://github.com/btschwertfeger/infinity-grid/actions/workflows/cicd.yaml/badge.svg?branch=master)](https://github.com/btschwertfeger/infinity-grid/actions/workflows/cicd.yaml)
[![codecov](https://codecov.io/gh/btschwertfeger/infinity-grid/branch/master/badge.svg)](https://app.codecov.io/gh/btschwertfeger/infinity-grid)

[![OpenSSF
ScoreCard](https://img.shields.io/ossf-scorecard/github.com/btschwertfeger/infinity-grid?label=openssf%20scorecard&style=flat)](https://securityscorecards.dev/viewer/?uri=github.com/btschwertfeger/infinity-grid)
[![OpenSSF Best
Practices](https://www.bestpractices.dev/projects/9956/badge)](https://www.bestpractices.dev/projects/9956)

[![release](https://shields.io/github/release-date/btschwertfeger/infinity-grid)](https://github.com/btschwertfeger/infinity-grid/releases)
[![release](https://img.shields.io/pypi/v/infinity-grid)](https://pypi.org/project/infinity-grid/)
[![Documentation Status Stable](https://readthedocs.org/projects/infinity-grid/badge/?version=stable)](https://infinity-grid.readthedocs.io/en/stable)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17034315.svg)](https://doi.org/10.5281/zenodo.17034315)

[![Telegram](https://img.shields.io/badge/Join_our_community-Telegram-blue?logo=telegram&logoColor=whiteg)](https://t.me/mx_infinity_grid)
[![Running instance](https://img.shields.io/badge/Preview_a_running_instance-Telegram-blue?logo=telegram&logoColor=whiteg)](https://t.me/mx_infinity_grid/3)

</div>

> ⚠️ **Disclaimer**: This software was initially designed for private use only.
> Please note that this project is independent and not endorsed by any of the
> supported exchanges including Kraken or Payward Ltd. Users should be aware
> that they are using third-party software, and the authors of this project are
> not responsible for any issues, losses, or risks associated with its usage.
> **The supported exchanges and their parent companies are in no way associated
> with the authors of this package and documentation.**
>
> _There is no guarantee that this software will work flawlessly at this or later
> times. Of course, no responsibility is taken for possible profits or losses.
> This software probably has some errors in it, so use it at your own risk. Also
> no one should be motivated or tempted to invest assets in speculative forms of
> investment. By using this software you release the author(s) from any
> liability regarding the use of this software._

The infinity-grid is a trading algorithm that uses grid trading strategies that
places buy and sell orders in a grid-like manner, while following the principle
of buying low and selling high. It is designed for trading cryptocurrencies,
stocks, and derivatives on various exchanges, initially only supporting
[Kraken](https://pro.kraken.com) Spot exchange with plans to expand to other
major exchanges, is written in Python and currently uses the
[python-kraken-sdk](https://github.com/btschwertfeger/python-kraken-sdk) library
to interact with the Kraken API, with additional exchange adapters planned.

The algorithm requires a PostgreSQL or SQLite database and is designed to be run
in a container. The algorithm can be configured to use different
trading strategies, such as GridHODL, GridSell, SWING, and cDCA. While the
verbosity levels of logging provide useful insights into the algorithms's
behavior, the custom notification channels such as Telegram can be used to
receive updates on the algorithms's activity.

Note: This project is the successor of the
[kraken-infinity-grid](https://github.com/btschwertfeger/kraken-infinity-grid).

**Documentation:**

- https://infinity-grid.readthedocs.io/en/latest/
- https://infinity-grid.readthedocs.io/en/stable/

**PnL Calculator (for tax purposes):**

- Kraken: https://github.com/btschwertfeger/kraken-pnl-calculator

**Product Support Matrix:**

| Exchange                                 | Status  |
| ---------------------------------------- | ------- |
| [Coinbase](https://binance.com)          | Planned |
| [Binance](https://binance.com)           | Planned |
| [Kraken](https://pro.kraken.com)         | ✅      |
| Other ideas? Issues and PRs are welcome! | 💡      |

## 📚 Fundamental concepts

`infinity-grid` is a sophisticated trading algorithm designed for
automated cryptocurrency trading using a grid strategy. This approach is
particularly effective in volatile markets, where frequent price fluctuations
allow for consistent profit opportunities through structured buying and selling
patterns.

### 📈 The core idea: Grid trading

At its essence, grid trading aims to capitalize on market volatility by setting
a series of buy and sell orders at predefined intervals. The algorithm operates
within a "grid" of prices, purchasing assets when prices dip and selling them as
prices rise. This systematic approach helps in capturing small gains repeatedly,
leveraging the natural oscillations in market prices.

<div align="center">
  <figure>
    <img
    src="doc/_static/images/blsh.png?raw=true"
    alt="Buying low and selling high in high-volatile markets"
    style="background-color: white; border-radius: 7px">
    <figcaption>Figure 1: Buying low and selling high in high-volatile markets</figcaption>
  </figure>
</div>

_All currency pairs mentioned here are for illustrative purposes only._

### 📊 Key Elements of Grid Trading

1. **Intervals**: Unlike fully static systems, `infinity-grid` uses fixed
   intervals that shift up or down based on price movements, ensuring continuous
   trading and avoids manual interactions. This flexibility is crucial for
   maintaining profitability in diverse market environments.

2. **Volatility Advantage**: High volatility is a friend to grid traders. The
   more the price oscillates, the more opportunities arise to buy low and sell
   high. The algorithm thrives in such conditions, with each price movement
   potentially triggering a profitable trade.

3. **Consistent Position Sizing**: Each trade involves a consistent volume in
   terms of the quote currency (e.g., $100 per trade). This uniformity
   simplifies the management of trades and helps in maintaining a balanced
   portfolio.

### 📉 Risk Management and Reinvestment

1. **Risk Mitigation**: The algorithm inherently incorporates risk management by
   spreading investments across multiple price levels and maintaining almost
   consistent trade sizes. This diversification reduces the impact of adverse
   market movements on the overall portfolio.

2. **Reinvestment Mechanism**: Accumulated profits can be reinvested, enhancing
   the trading capital and potential returns. The algorithm automatically
   adjusts buy and and places sell orders to reflect the increased capital, thus
   compounding growth over time.

## 📊 Available strategies

Each of the following strategies is designed to leverage different aspects of
market behavior, providing flexibility and adaptability to traders depending on
their risk tolerance, market outlook, and investment goals.

### `GridHODL`

The _GridHODL_ strategy operates on a predefined grid system where buy and sell
orders are placed at fixed intervals below and above the current market price,
respectively. This strategy is designed to capitalize on market fluctuations by
buying low and selling high, ensuring gradual accumulation of the base currency
over time.

Technical Breakdown:

- **Order Placement**: The algorithm dynamically adjusts $n$ buy orders below
  the current market price. For example, with a 4% interval, if the current BTC
  price is $50,000, the first buy order is set at $48,000, the second at
  $46,080, and so on.
- **Execution**: Upon execution of a buy order, a corresponding sell order is
  immediately placed at 4% above the purchase price respecting a fixed quote
  volume. This creates a cycle of continuous buying and selling, with each cycle
  aiming to yield a small portion in the base currency.
- **Accumulation**: Unlike traditional trading strategies, GridHODL is designed
  to accumulate the base currency gradually. Each buy order slightly increases
  the holdings, while the fixed order size in terms of quote currency (e.g.,
  $100) ensures consistent exposure.

This strategy is particularly effective in sideways, slightly, and high volatile
markets, where frequent price oscillations allow for regular execution of the
grid orders. Accumulating the base currency over time can lead to significant
gains, especially when prices rise after a long accumulation phase.

### `GridSell`

The _GridSell_ is a complementary approach to `GridHODL`, focusing on
liquidating the purchased base currency in each trade cycle to realize immediate
profits. The key distinction is that each sell order matches the total quantity
bought in the preceding buy order.

Technical Breakdown:

- **Order Logic**: For every buy order executed (e.g., purchasing $100 worth of
  BTC at $48,000), a sell order is placed for the entire amount of BTC acquired
  at a 4% higher price. This ensures that each trade cycle results in a complete
  turnover of the base currency.
- **Profit Realization**: The strategy ensures that profits are locked in at
  each cycle, reducing the need for long-term accumulation or holding. It is
  particularly suitable for traders who prioritize short-term gains over base
  currency accumulation.
- **Risk Mitigation**: By liquidating the entire bought amount, the GridSell
  strategy minimizes exposure to prolonged market downturns, ensuring that the
  trader consistently realizes profits without holding onto assets for extended
  periods.

### `SWING`

The _SWING_ strategy builds upon `GridHODL` but introduces a mechanism to
capitalize on significant upward price movements by selling accumulated base
currency at higher levels.

Technical Breakdown:

- **Market Adaptation**: This strategy tracks the highest buy price within a
  defined range (e.g., $40,000 to $80,000). If the market price exceeds this
  range (e.g., rises to $83,200), the algorithm initiates sell orders at
  predefined intervals (e.g., 4% above the highest buy price).
- **Sell Execution**: Unlike `GridHODL`, which focuses on buying and selling in
  cycles, SWING starts selling accumulated base currency once the price
  surpasses the highest recorded buy price. This ensures that profits are
  captured during bullish market trends.
- **Continuous Accumulation**: Even as it initiates sell orders above the
  highest buy price, the algorithm continues to place buy orders below it,
  ensuring that base currency accumulation continues during market dips.
- **Profit Maximization**: This dual approach allows traders to benefit from
  both upward trends (through sell orders) and downward corrections (through
  continued accumulation).

> ⚠️ It also starts selling the already existing base currency above the current
> price. This should be kept in mind when choosing this strategy.

### `cDCA`

The _cDCA_ (Custom Dollar-Cost Averaging) strategy diverges from traditional DCA
by incorporating dynamic interval adjustments to optimize long-term accumulation
of the base currency.

Technical Breakdown:

- **Fixed Interval Purchases**: Unlike time-based DCA, cDCA places buy orders at
  fixed percentage intervals (e.g., every 4% price movement) rather than at
  regular time intervals. This ensures that purchases are made in response to
  market movements rather than arbitrary time frames.
- **No Sell Orders**: cDCA focuses purely on accumulation. It consistently buys
  the base currency (e.g., $100 worth of BTC) at each interval without placing
  corresponding sell orders, banking on long-term price appreciation.
- **Adaptive Buy Orders**: The algorithm adapts to rising prices by shifting buy
  orders upward rather than letting them fall out of scope. For instance, if the
  price exceeds $60,000, new buy orders are placed at 4% intervals below this
  new level, maintaining relevance in the current market context.
- **Long-Term Growth**: This strategy is ideal for traders with a long-term
  investment horizon, aiming to build a significant position in the base
  currency over time, with the expectation of future price increases.

<a name="setup"></a>

## 🚀 Setup

<a name="preparation"></a>

### Preparation

Before installing and running the `infinity-grid` algorithm, you need to make
sure to fully understand the available trading strategies and their
configuration. Avoid running the algorithm with real money before you are
confident in the algorithm's behavior and performance!

Depending on the used exchange, different preparatory steps might be needed. In
the following, the steps for use with the Kraken Crypto Asset Exchange is shown:

1. In order to trade at the [Kraken Crypto Asset
   Exchange](https://pro.kraken.com), you need to generate API keys for the
   Kraken exchange (see [How to create an API
   key](https://support.kraken.com/hc/en-us/articles/360000919966-How-to-create-an-API-key)).
   Make sure to generate keys with the required permissions for trading and
   querying orders:

<div align="center">
  <figure>
    <img
    src="doc/_static/images/kraken_api_key_permissions.png?raw=true"
    alt="Required API key permissions"
    style="background-color: white; border-radius: 7px">
    <figcaption>Figure 2: Required API key permissions</figcaption>
  </figure>
</div>

2. [optional] The algorithm leverages Telegram Bots to send notifications about
   the current state of the algorithm. We need two, one for the notifications
   about the algorithm's state and trades and one for notifications about
   errors.

   - Create two bots, name as you wish via: https://telegram.me/BotFather.
   - Start the chat with both new Telegram bots and write any message to ensure
     that the chat ID is available in the next step.
   - Get the bot token from the BotFather and access
     `https://api.telegram.org/bot<your bot token here>/getUpdates` to receive
     your chat ID.
   - Save the chat IDs as well as the bot tokens for both of them, we'll need
     them later.

### Running the algorithm

The repository of the
[`infinity-grid`](https://github.com/btschwertfeger/infinity-grid)
contains a `docker-compose.yaml` file that can be used to run the algorithm
using Docker Compose. This file also provides a default configuration for the
PostgreSQL database. To run the algorithm, ensure the required environment
variables are set and start the containers using:

```console
docker compose up -d
```

## 🛠 Configuration

The most important configuration options are shown in the table below. The
infinity-grid leverages [click](https://click.palletsprojects.com/en/stable)'s
`auto_envvar_prefix` to map environment variables to command-line options,
flags, and inputs. The complete list of options available can be obtained by
running `infinity-grid --help` or `infinity-grid run --help`.

| Variable                               | Type               | Description                                                                                                                                                                                                                                                                                                    |
| -------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `INFINITY_GRID_API_PUBLIC_KEY`         | `str`              | The API public key provided by the exchange.                                                                                                                                                                                                                                                                   |
| `INFINITY_GRID_API_SECRET_KEY`         | `str`              | The API secret key provided by the exchange.                                                                                                                                                                                                                                                                   |
| `INFINITY_GRID_RUN_EXCHANGE`           | `str`              | The exchange to trade on.                                                                                                                                                                                                                                                                                      |
| `INFINITY_GRID_RUN_NAME`               | `str`              | The name of the instance. Can be any name that is used to differentiate between instances of the infinity-grid.                                                                                                                                                                                                |
| `INFINITY_GRID_RUN_USERREF`            | `int`              | A reference number to identify the algorithms's orders. This can be a timestamp or any integer number. **Use different userref's for different algorithms!**                                                                                                                                                   |
| `INFINITY_GRID_BOT_VERBOSE`            | `int`/(`-v`,`-vv`) | Enable verbose logging.                                                                                                                                                                                                                                                                                        |
| `INFINITY_GRID_RUN_BASE_CURRENCY`      | `str`              | The base currency e.g., `BTC` or `AVAX`.                                                                                                                                                                                                                                                                       |
| `INFINITY_GRID_RUN_QUOTE_CURRENCY`     | `str`              | The quote currency e.g., `USD` or `EUR`.                                                                                                                                                                                                                                                                       |
| `INFINITY_GRID_RUN_AMOUNT_PER_GRID`    | `float`            | The amount to use per grid interval e.g., `100` (USD).                                                                                                                                                                                                                                                         |
| `INFINITY_GRID_RUN_INTERVAL`           | `float`            | The interval between orders e.g., `0.04` to have 4 % intervals.                                                                                                                                                                                                                                                |
| `INFINITY_GRID_RUN_N_OPEN_BUY_ORDERS`  | `int`              | The number of concurrent open buy orders e.g., `5`. The number of always open buy positions specifies how many buy positions should be open at the same time. If the interval is defined to 2%, a number of 5 open buy positions ensures that a rapid price drop of almost 10% that can be caught immediately. |
| `INFINITY_GRID_RUN_MAX_INVESTMENT`     | `str`              | The maximum investment amount, e.g. `1000` USD.                                                                                                                                                                                                                                                                |
| `INFINITY_GRID_RUN_FEE`                | `float`            | A custom fee percentage, e.g. `0.0026` for 0.26 % fee.                                                                                                                                                                                                                                                         |
| `INFINITY_GRID_RUN_STRATEGY`           | `str`              | The trading strategy (e.g., `GridHODL`, `GridSell`, `SWING`, or `cDCA`).                                                                                                                                                                                                                                       |
| `INFINITY_GRID_DRY_RUN`                | `bool`             | Enable dry-run mode (no actual trades).                                                                                                                                                                                                                                                                        |
| `INFINITY_GRID_RUN_SKIP_PRICE_TIMEOUT` | `bool`             | Skip checking if there was a price update in the last 10 minutes. By default, the bot will exit if no recent price data is available. This might be useful for assets that aren't traded that often.                                                                                                           |
| `INFINITY_GRID_RUN_TELEGRAM_TOKEN`     | `str`              | The Telegram bot token for notifications.                                                                                                                                                                                                                                                                      |
| `INFINITY_GRID_RUN_TELEGRAM_CHAT_ID`   | `str`              | The Telegram chat ID for notifications.                                                                                                                                                                                                                                                                        |
| `INFINITY_GRID_RUN_TELEGRAM_THREAD_ID` | `str`              | The Telegram thread ID for notifications.                                                                                                                                                                                                                                                                      |
| `INFINITY_GRID_RUN_DB_USER`            | `str`              | The PostgreSQL database user.                                                                                                                                                                                                                                                                                  |
| `INFINITY_GRID_RUN_DB_NAME`            | `str`              | The PostgreSQL database name.                                                                                                                                                                                                                                                                                  |
| `INFINITY_GRID_RUN_DB_PASSWORD`        | `str`              | The PostgreSQL database password.                                                                                                                                                                                                                                                                              |
| `INFINITY_GRID_RUN_DB_HOST`            | `str`              | The PostgreSQL database host.                                                                                                                                                                                                                                                                                  |
| `INFINITY_GRID_RUN_DB_PORT`            | `int`              | The PostgreSQL database port.                                                                                                                                                                                                                                                                                  |
| `INFINITY_GRID_RUN_SQLITE_FILE`        | `str`              | The path to a local SQLite database file, e.g., `/path/to/sqlite.db`, will be created if it does not exist. If a SQLite database is used, the PostgreSQL database configuration is ignored.                                                                                                                    |

<a name="monitoring"></a>

## 📡 Monitoring

Trades as well as open positions can be monitored at the exchanges', where they
can also be managed. Keep in mind that canceling via UI is possible, but placing
orders that the algorithm will manage is not possible, as it only manages orders
that it has placed, e.g. for the Kraken Crypto Asset exchange at
https://pro.kraken.com.

<div align="center">
  <figure>
    <img
    src="doc/_static/images/kraken_dashboard.png?raw=true"
    alt="Required API key permissions"
    style="background-color: white; border-radius: 7px">
    <figcaption>Figure 3: Monitoring orders via Kraken's web UI</figcaption>
  </figure>
</div>

Additionally, the algorithm can be configured to send notifications regarding
the current state of the algorithm via Telegram Bots (see
[Preparation](#preparation)).

<div align="center">
  <figure>
    <img
    src="doc/_static/images/telegram_update.png?raw=true"
    alt="Required API key permissions"
    style="background-color: white; border-radius: 7px; height: 500px">
    <figcaption>Figure 4: Monitoring orders and trades via Telegram</figcaption>
  </figure>
</div>

## 🚨 Troubleshooting

- Only use release versions of the `infinity-grid` algorithm. The `master` and
  other branches might contain unstable code! Also pin the the dependencies used
  in order to avoid unexpected behavior.
- Check the **permissions of your API keys** and the required permissions on the
  respective endpoints of your chosen exchange.
- If you get some Cloudflare or **rate limit errors**, please check your tier
  level on your exchange and maybe apply for a higher rank if required.
- **Use different API keys for different algorithms**, because the nonce
  calculation is based on timestamps and a sent nonce must always be the highest
  nonce ever sent of that API key. Having multiple algorithms using the same
  keys will result in invalid nonce errors.
- Exchanges often have **maintenance windows**. Please check the status page of
  your exchange for more information.
- When encountering errors like "Could not find order '...'. Retry 3/3 ...",
  this might be due to the **exchange API being slow**. The algorithm will retry
  the request up to three times before raising an exception. If the order is
  still not available, just restart the algorithm - or let this be handled by
  Docker compose to restart the container automatically. Then the order will
  most probably be found.
- Always use unique user reference keys/numbers for each trading bot instance.
  The algorithm will know what orders to handle based on passed user reference
  numbers and selected trading pair.

## 📈 Backtesting

There are currently no backtesting mechanisms implemented. This will be added
soon.

<a name="notes"></a>

## 📝 Notes

This project follows the principles of [semantic
versioning](https://semver.org/) (`v<Major>.<Minor>.<Patch>`). Here's what each
part signifies:

- **Major**: This denotes significant changes that may introduce new features or
  modify existing ones. It's possible for these changes to be breaking, meaning
  backward compatibility is not guaranteed. To avoid unexpected behavior, it's
  advisable to specify at least the major version when pinning dependencies.
- **Minor**: This level indicates additions of new features or extensions to
  existing ones. Typically, these changes do not break existing implementations.
- **Patch**: Here, you'll find bug fixes, documentation updates, and changes
  related to continuous integration (CI). These updates are intended to enhance
  stability and reliability without altering existing functionality.
