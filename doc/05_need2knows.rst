.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2025 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

.. _need2knows-section:

Need 2 Knows
============

This is a section of the documentation that contains some useful information
that might be worth noting.

🧮 Hidden tax benefits
----------------------

.. WARNING:: This is no financial advice. The authors of this software are not
             tax advisors. The following scenario may not apply universally.
             Users should conduct their own research.

In many countries, the tax principle of First In, First Out (FIFO) is applied to
cryptocurrency trading. The ``infinity-grid`` benefits from this, as the first
purchased assets are the first to be sold. This means that in sideways or
downward-trending markets over the medium to long term, sell orders may
liquidate assets bought at higher price levels (from a tax perspective).
Consequently, even if actual profits are made by selling at a higher price than
the last buy order, no taxes may be due, as the transaction could be considered
a loss for tax purposes. This approach can be utilized to accumulate
cryptocurrencies in declining markets, such as with the :ref:`GridHODL`
strategy, potentially without incurring any tax liabilities.

🤖 Terminating a running instance
---------------------------------

The infinity-grid trading bot is designed to be safe to terminate. When a
``SIGTERM`` or ``SIGINT`` is received, the instance stops processing incoming
websocket messages, finalizes is current tasks, e.g. creating an order, waiting
for an order to be processed and saved in the DB etc. Thus, no data is lost when
the algorithm was stopped this way.

In case the algorithm gets stopped differently there is a chance of misbehavior,
so please avoid such scenarios and terminate the instance the normal way like:

- ``docker compose down``
- ``CTRL + C`` / ``Command + C``

📲 Updating to a new version
----------------------------

The infinity-grid follows semantic versioning, meaning that updating the image
used can be done by increasing the minor or patch level of the tag. It is still
recommended to read the `changelog`_.

For updates to new major versions, reading the changelog is essential. There we
will have a migration guide or refer to a guide that demonstrates how to
proceed.

📋 What happens to partially filled buy orders?
-----------------------------------------------

The algorithm manages its orders in lean way, meaning partially filled buy
orders that may get cancelled will be remembered. This is done internally by
saving the order price and filled amount in order to place a sell order at a
higher price in the future.

💡 Further things to know
-------------------------

- The trading bot allows the use of an *in-memory database*. Only use this for
  testing and debugging purposes, since information gets lost after the instance
  was terminated.
- Using *SQLite* as DB for a single instance might be appealing, but can slow down
  the trading bot and is not as stable as running against a real PostgreSQL
  instance. Using a PostgreSQL DB backend is the recommended way as it also
  allows running multiple trading bot instances against the same DB backend.
- *Use different userref's for different bot instances*. The userref is used by
  the bot to identify which orders belong to him. Using the same usererf for
  different assets or running multiple bot instances for the same or different
  asset pairs using the same userref will result in errors.

🐙 Kraken Crypto Asset Exchange
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Use different API keys for different bot instances, otherwise you will
  encounter nonce calculation errors.

⚒️ Useful tools
---------------

- Kraken PnL Calculator (for tax purposes): https://github.com/btschwertfeger/kraken-pnl-calculator
