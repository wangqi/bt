import bt


class SelectByRange(bt.algos.Algo):
    """
      Select an security only if its price changes rate is +10% since last selection.
    """

    def __init__(self, high_limit=0.0, low_limit=-0.0):
        super(SelectByRange, self).__init__()
        self.high_limit = high_limit
        self.low_limit = low_limit
        self.initial_prices = None

    def __call__(self, target):
        universe = target.universe.loc[target.now].dropna()
        if self.initial_prices is None:
            # set the inital prices
            self.initial_prices = universe.copy()
            target.temp['selected'] = list(universe[universe > 0].index)
            return True
        else:
            change_rates = (universe - self.initial_prices) / self.initial_prices
            selected = (change_rates > self.high_limit) | (change_rates < self.low_limit)
            selected_list = list(selected[selected == True].index)
            if len(selected_list) <= 0:
                return False
            else:
                target.temp['selected'] = selected_list
                # remember the new prices
                self.initial_prices = universe.copy()



data = bt.get('SPTL, GLD, QQQ, SHY', start='2019-01-01')
sma = data.rolling(50).mean()

signal = data > sma
signal.head(10)
sig = signal.loc['2019-05-31']
print(sig)
list(sig.index[sig])

s = bt.Strategy('above50sma', [bt.algos.RunMonthly(),
                               SelectByRange(high_limit=0.1, low_limit=-0.1),
                               # bt.algos.SelectAll(),
                               bt.algos.WeighEqually(),
                               bt.algos.Rebalance()])
t = bt.Backtest(s, data)
res = bt.run(t)
print(res.get_transactions())
