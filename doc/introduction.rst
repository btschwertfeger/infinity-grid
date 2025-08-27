.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2023 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

Introduction
============

|GitHub badge| |PyVersions badge| |Downloads badge|
|CI/CD badge| |Typing badge| |codecov badge|
|Release date badge| |Release version badge| |DOI badge|


Disclaimer
----------

⚠️ **Disclaimer**: This software was initially designed for private use only.
Please note that this project is independent and not endorsed by any of the
supported exchanges including Kraken or Payward Ltd. Users should be aware
that they are using third-party software, and the authors of this project are
not responsible for any issues, losses, or risks associated with its usage.
**The supported exchanges and their parent companies are in no way associated
with the authors of this package and documentation.**

*There is no guarantee that this software will work flawlessly at this or later
times. Of course, no responsibility is taken for possible profits or losses.
This software probably has some errors in it, so use it at your own risk. Also
no one should be motivated or tempted to invest assets in speculative forms of
investment. By using this software you release the author(s) from any
liability regarding the use of this software.*

Overview
--------

The infinity-grid is a trading algorithm that uses grid trading strategies that
places buy and sell orders in a grid-like manner, while following the principle
of buying low and selling high. It is designed for trading cryptocurrencies on
various exchanges, initially supporting `Kraken`_ Spot exchange with plans to
expand to other major exchanges, is written in Python and currently uses the
`python-kraken-sdk`_ library to interact with the Kraken API, with additional
exchange adapters planned.

The algorithm requires a PostgreSQL or SQLite database and can be run either
locally or in a Docker container (recommended). The algorithm can be configured
to use different trading strategies, such as :ref:`GridHODL
<strategies-gridhodl-section>`, :ref:`GridSell <strategies-gridsell-section>`,
:ref:`SWING <strategies-swing-section>`, and :ref:`cDCA
<strategies-cdca-section>`.

While the verbosity levels of logging provide useful insights into the
algorithm's behavior, the optional Telegram notifications can be used to receive
updates on the algorithm's activity and exceptions. For this, the algorithm
requires two different Telegram bot tokens and chat IDs, one for regular
notifications and one for exception notifications (see :ref:`Getting started
<getting-started-section>` for more information).

Troubleshooting
---------------

- Only use release versions of the ``infinity-grid``. The ``master``
  branch might contain unstable code! Also pin the the dependencies used in
  order to avoid unexpected behavior.
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
- Feel free to open an issue at `infinity-grid/issues`_.

References
----------

- https://python-kraken-sdk.readthedocs.io/en/stable
- https://docs.kraken.com/api/
- https://docs.kraken.com/rest
- https://docs.kraken.com/websockets-v2
