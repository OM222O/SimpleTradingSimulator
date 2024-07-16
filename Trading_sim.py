import sys
from collections import defaultdict
from statistics import geometric_mean
from datetime import datetime, timedelta, UTC


# Required version: Python 3.10+
# Tested with: Python 3.12


def to_str(instance):
    return f'{type(instance).__name__}({", ".join([f"{slot}: {getattr(instance, slot)}" for slot in getattr(instance, "__slots__", [])])})'


class Stock:
    __slots__ = 'symbol', 'typ', 'last_div', 'fixed_div', 'par_value'

    def __init__(self, symbol, typ, last_div, fixed_div, par_value):
        if None in (symbol, typ, last_div, par_value):
            raise ValueError('Mandatory fields (symbol, type, last_div, par_value) cannot be None!')
        typ = typ.lower()
        if typ == 'preferred':
            if fixed_div is None:
                raise ValueError('fixed_div cannot be None for preferred stock!')
            else:
                fixed_div = int(fixed_div)
        last_div = int(last_div)
        par_value = int(par_value)

        self.symbol = symbol
        self.typ = typ
        self.last_div = last_div
        self.fixed_div = fixed_div
        self.par_value = par_value

    def __str__(self):
        return to_str(self)

    def __repr__(self):
        return self.__str__()


class Trade:
    __slots__ = 'instant', 'stock', 'is_buy', 'qty', 'price'

    def __init__(self, stock, indicator, qty, price):
        self.instant = datetime.now(UTC)
        qty = int(qty)
        price = float(price)
        if None in (stock, indicator, qty, price):
            raise ValueError('Mandatory fields (stock, indicator, qty, price) cannot be None!')
        if qty <= 0 or price <= 0:
            raise ValueError('Price and quantity must be greater than 0')
        indicator = indicator.lower()
        if indicator not in ('buy', 'sell'):
            raise ValueError(f'Invalid buy/sell indicator {indicator}')
        self.stock = stock
        self.is_buy = indicator == 'buy'
        self.qty = qty
        self.price = price

    def __str__(self):
        return to_str(self)

    def __repr__(self):
        return self.__str__()


def buy(stock, qty, price):
    """Creates a buy trade against the provided stock for the given quantity and price.
    For example to buy 5 tea at a price of 1.2 per share, type: buy TEA 5 1.2"""
    return Trade(stock, 'buy', qty, price)


def sell(stock, qty, price):
    """Similar to buy command, but it creates a sell trade instead"""
    return Trade(stock, 'sell', qty, price)


def calc_div_yield(stock, price):
    """Calculates dividend yield for the given stock and price. Example: dividend_yield POP 2"""
    if price <= 0:
        raise valueError('Price must be greater than 0')
    if stock.typ.lower() == 'common':
        return stock.last_div / price
    else:
        # divide by 100 because fixed_div is a percentage
        return (stock.fixed_div * stock.par_value) / (price * 100)


def calc_ratio():
    """NOT YET IMPLEMENTED"""
    return 0


def calc_volume_weighted_price(stock, trades):
    """Calculates the volume weighted stock price for the given stock based on
    trading activity in the past 5 minutes. Example: volume_weighted_price ALE"""
    cutoff_date = datetime.now(UTC) - timedelta(minutes=5)
    weighted_price = 0
    volume = 0
    for trade in trades:
        if trade.instant > cutoff_date and trade.stock.symbol == stock.symbol:
            weighted_price += trade.price * trade.qty
            volume += trade.qty
    if volume == 0:
        raise ValueError(f"Couldn't find any trading activity for {stock.symbol}!")
    return weighted_price / volume


def gbce(stocks, trades):
    """Calculates the GBCE all share index for all stocks with trading activity"""
    volume_weighted_prices = []
    for symbol in stocks:
        try:
            volume_weighted_prices.append(calc_volume_weighted_price(stocks[symbol], trades))
        except ValueError as e:
            if not str(e).startswith("Couldn't find any trading activity"):
                raise e
    if len(volume_weighted_prices) == 0:
        raise ValueError("Couldn't find any trading activity for any stock!")
    return geometric_mean(volume_weighted_prices)


def print_help():
    """Prints help"""
    for action, fn in actions.items():
        print(f'{action}: {fn.__doc__ or "No help available"}')


def q():
    """Quits the program"""
    print('Exiting ...')


def pretty_print(iterable):
    count = 0
    for item in iterable:
        count += 1
        print(str(item))
    if count == 0:
        print('No items to show!')


def validate_symbol(symbol, stocks):
    if symbol not in stocks:
        raise ValueError(f'Invalid stock symbol({symbol}). Choose from: {list(stocks)}')


if __name__ == '__main__':
    actions = {
        'help': print_help,
        'dividend_yield': calc_div_yield,
        'p_to_e_ratio': calc_ratio,
        'buy': buy,
        'sell': sell,
        'volume_weighted_price': calc_volume_weighted_price,
        'gbce': gbce,
        'show_trades': pretty_print,
        'show_stocks': pretty_print,
        'exit': q,
        'quit': q
    }

    stocks = {
        stock.symbol: stock for stock in [
            Stock('TEA', 'common', 0, None, 100),
            Stock('POP', 'common', 8, None, 100),
            Stock('ALE', 'common', 23, None, 60),
            Stock('GIN', 'preferred', 8, 2, 100),
            Stock('JOE', 'common', 13, None, 250),
        ]
    }

    trades = []

    print('Basic trading app simulator')
    print('#' * 20)
    print('Available stocks are:')
    pretty_print(stocks.values())
    print('#' * 20)
    print('Available actions are:')
    print_help()
    print('#' * 20)

    while True:
        try:
            action, *args = input('What would you like to do?\n').strip().split()
            action = action.lower()
            on_exit = lambda _: None
            print_result = True
            if action in actions:
                if actions[action] is q:
                    break
                match action:
                    case 'buy' | 'sell':
                        symbol = args[0]
                        validate_symbol(symbol, stocks)
                        args[0] = stocks[symbol]
                        on_exit = lambda trade: trades.append(trade)
                    case 'dividend_yield':
                        symbol = args[0]
                        validate_symbol(symbol, stocks)
                        args = [stocks[symbol], float(args[1])]
                    case 'volume_weighted_price':
                        symbol = args[0]
                        validate_symbol(symbol, stocks)
                        args = [stocks[symbol], trades]
                    case 'gbce':
                        args = [stocks, trades]
                    case 'show_trades':
                        args = [trades]
                        print_result = False
                    case 'show_stocks':
                        args = [stocks.values()]
                        print_result = False
                result = actions[action](*args)
                if print_result:
                    print(f'Result: {result}')
                on_exit(result)
            else:
                print(f'Invalid action! choose from: {list(actions.keys())}')
        except (ValueError, TypeError) as e:
            print(e)
