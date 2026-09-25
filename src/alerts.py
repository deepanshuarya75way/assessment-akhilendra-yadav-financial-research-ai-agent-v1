import yfinance as yf

def normalize_alert_symbol(symbol):
  symbol = symbol.strip().upper()

  if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
    symbol = f"{symbol}.NS"

    return symbol


    def get_latest_price(symbol):
      symbol = normalize_alert_symbol(symbol)

      data = yf.Ticker(symbol).history(period="5d", interval="1d")

      if data.empty or "Close" not in data.columns:
        return None

        close_prices = data["Close"].dropna()

        if close_prices.empty:
          return None

          return float(close_prices.iloc[-1])


          def is_alert_triggered(symbol, condition_type, target_value):
            latest_price = get_latest_price(symbol)

            if latest_price is None:
              return False, None, f"No market data found for {symbol}"

               target_value = float(target_value)

               if condition_type == "Price above":
                triggered = latest_price >= target_value
                elif condition_type == "Price below":
                  triggered = latest_price <= target_value
                  else:
                    return False, latest_price, "Unknown alert condition"

                    if triggered:
                      message = (
                        f"{normalize_alert_symbol(symbol)} price is "
                        f"{latest_price:.2f}. Alert target: {target_value:.2f}"
                      )
                      return True,latest_price,message

                      return False,latedt_price,None