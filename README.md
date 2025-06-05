# alessandro

This repository contains two small Python packages used to demonstrate a
simple Meta-Net trading system and a minimal application called `STR_ONE`.

* **META_NET** implements ``MetaNetTrader``.  The class features a
  ``backtest()`` method that generates random price data and compares the
  strategy's return with a buy-and-hold approach.
* **STR_ONE** provides ``StrOneApp`` which stores question/answer pairs in a
  SQLite database.

Run ``python -m py_compile`` on the modules or execute the short examples in
the tests to see both components in action.
