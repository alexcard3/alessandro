# alessandro

This repository contains two small Python packages used to demonstrate a
simple Meta-Net trading system and a minimal application called `STR_ONE`.

* **META_NET** implements ``MetaNetTrader``. The class features a
  ``backtest()`` method that generates random price data and compares the
  strategy's return with a buy-and-hold approach.
* **STR_ONE** provides ``StrOneApp`` which stores question/answer pairs in a
  SQLite database and exposes ``MetaNetManager`` with pluggable trading bots.

Run ``python -m py_compile`` on the modules or execute the short examples in
the tests to see both components in action. Bots live in ``str_one.bots``; the
included ``TrendFollowingBot``, ``BreakoutStrategyBot`` and ``MeanReversionBot``
demonstrate how to feed signals into the manager. A more advanced example,
``BTC4H5MBot``, shows how to adapt a real trading script to the same
interface.

## Running tests

Execute the test suite with::

    python -m unittest
