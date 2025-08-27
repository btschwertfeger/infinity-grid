.. -*- mode: rst; coding: utf-8 -*-
..
.. Copyright (C) 2025 Benjamin Thomas Schwertfeger
.. All rights reserved.
.. https://github.com/btschwertfeger
..

.. _need2knows-section:

Need 2 Knows
============

This is a section of the documentation that contains important information
that you need to know. It is important to read this section before you
begin using the software.

What happens to partially filled buy orders?
--------------------------------------------

The algorithm manages its orders in lean way, meaning partially filled buy orders
that may get cancelled will be remembered. This is done internally by saving the
order price and filled amount in order to place a sell order at a higher price
in the future.

The log shows closed connection but the algorithm is still running
------------------------------------------------------------------

In a case where a traceback or warning containing something like "got an
exception no close frame received or sent" is shown in the log, the algorithm
will keep running, as the underlying `python-kraken-sdk`_ library handles the
reconnect.

In case of uncertainty, the ``infinity-grid`` can be started with verbose
logging to see the reconnection process (and more). The verbose logging can be
enabled via ``-v`` for debug logging of the ``infinity-grid`` or ``-vv`` for
even more logging of used packages.

Hidden tax benefits
-------------------

.. WARNING:: This is no financial advice. The authors of this software are not
             tax advisors. The following scenario may not apply universally.
             Users should conduct their own research.

In many countries, the tax principle of First In, First Out (FIFO) is applied to
cryptocurrency trading. The ``infinity-grid`` benefits from this, as the
first purchased assets are the first to be sold. This means that in sideways or
downward-trending markets over the medium to long term, sell orders may
liquidate assets bought at higher price levels (from a tax perspective).
Consequently, even if actual profits are made by selling at a higher price than
the last buy order, no taxes may be due, as the transaction could be considered
a loss for tax purposes. This approach can be utilized to accumulate
cryptocurrencies in declining markets, such as with the :ref:`GridHODL`
strategy, potentially without incurring any tax liabilities.

Useful tools
------------

- Kraken PnL Calculator (for tax purposes): https://github.com/btschwertfeger/kraken-pnl-calculator
