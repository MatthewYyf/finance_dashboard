import yfinance as yf


def get_current_prices(symbols: list[str]) -> dict[str, float]:
    prices = {}

    if not symbols:
        return prices

    tickers = yf.Tickers(" ".join(symbols))

    for symbol in symbols:
        try:
            ticker = tickers.tickers[symbol]
            info = ticker.fast_info
            last_price = info.get("lastPrice")

            if last_price is not None:
                prices[symbol] = float(last_price)
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")

    return prices