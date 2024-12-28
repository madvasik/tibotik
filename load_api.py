import os
from datetime import timedelta
import pandas as pd
from indicators import calculate_all_indicators

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

from pandas import DataFrame

from tinkoff.invest import Client, SecurityTradingStatus
from tinkoff.invest.services import InstrumentsService
from tinkoff.invest.utils import quotation_to_decimal

def units_nano_to_num(candle_arg):
    return candle_arg.units + candle_arg.nano / 1000000000

def load_df(TOKEN, figi='BBG004S683W7', days=100, lot=1):
    d = {
        'Date': [],
        'Open': [],
        'High': [],
        'Low': [],
        'Close': [],
        'Vol': []
    }
    with Client(TOKEN) as client:
        for candle in client.get_all_candles(
            figi=figi,
            from_=now() - timedelta(days=days),
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        ):
            d['Date'].append(candle.time)
            d['Open'].append(units_nano_to_num(candle.open))
            d['High'].append(units_nano_to_num(candle.high))
            d['Low'].append(units_nano_to_num(candle.low))
            d['Close'].append(units_nano_to_num(candle.close))
            d['Vol'].append(candle.volume*lot)
    df = pd.DataFrame.from_dict(d)
    df = calculate_all_indicators(df)
    return df

def get_figi_by_ticker(TOKEN, ticker):
    with Client(TOKEN) as client:
        instruments: InstrumentsService = client.instruments
        tickers = []
        for method in ["shares", "bonds", "etfs", "currencies", "futures"]:
            for item in getattr(instruments, method)().instruments:
                tickers.append(
                    {
                        "name": item.name,
                        "ticker": item.ticker,
                        "class_code": item.class_code,
                        "figi": item.figi,
                        "uid": item.uid,
                        "type": method,
                        "min_price_increment": quotation_to_decimal(
                            item.min_price_increment
                        ),
                        "scale": 9 - len(str(item.min_price_increment.nano)) + 1,
                        "lot": item.lot,
                        "trading_status": str(
                            SecurityTradingStatus(item.trading_status).name
                        ),
                        "api_trade_available_flag": item.api_trade_available_flag,
                        "currency": item.currency,
                        "exchange": item.exchange,
                        "buy_available_flag": item.buy_available_flag,
                        "sell_available_flag": item.sell_available_flag,
                        "short_enabled_flag": item.short_enabled_flag,
                        "klong": quotation_to_decimal(item.klong),
                        "kshort": quotation_to_decimal(item.kshort),
                    }
                )

        tickers_df = DataFrame(tickers)

        ticker_df = tickers_df[tickers_df["ticker"] == ticker]


        figi = ticker_df["figi"].iloc[0]
        return figi
