import copy

from bt.core import Node, StrategyBase, SecurityBase, Strategy
import pandas as pd


def test_node_tree():
    c1 = Node('c1')
    c2 = Node('c2')
    p = Node('p', children=[c1, c2])

    assert len(p.children) == 2
    assert 'c1' in p.children
    assert 'c2' in p.children
    assert p == c1.parent
    assert p == c2.parent

    m = Node('m', children=[p])

    assert len(m.children) == 1
    assert 'p' in m.children
    assert p.parent == m
    assert len(p.children) == 2
    assert 'c1' in p.children
    assert 'c2' in p.children
    assert p == c1.parent
    assert p == c2.parent


def test_strategybase_tree():
    s1 = SecurityBase('s1')
    s2 = SecurityBase('s2')
    s = StrategyBase('p', [s1, s2])

    assert len(s.children) == 2
    assert 's1' in s.children
    assert 's2' in s.children
    assert s == s1.parent
    assert s == s2.parent


def test_security_setup_prices():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[0]] = 105
    data['c2'][dts[0]] = 95

    s.setup(dts)

    i = 0
    s.update(dts[i], data.ix[dts[i]])

    assert c1.price == 105
    assert len(c1.prices) == 1
    assert c1.prices[0] == 105

    assert c2.price == 95
    assert len(c2.prices) == 1
    assert c2.prices[0] == 95

    # now with setup
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])
    c1 = s['c1']
    c2 = s['c2']

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[0]] = 105
    data['c2'][dts[0]] = 95

    s.setup(dts)
    c1.setup(dts, data['c1'])
    c2.setup(dts, data['c2'])

    i = 0
    s.update(dts[i], data.ix[dts[i]])

    assert c1.price == 105
    assert len(c1.prices) == 1
    assert c1.prices[0] == 105

    assert c2.price == 95
    assert len(c2.prices) == 1
    assert c2.prices[0] == 95


def test_strategybase_tree_setup():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    assert len(s.data) == 3
    assert len(c1.data) == 3
    assert len(c2.data) == 3

    assert len(s.prices) == 0
    assert len(c1.prices) == 0
    assert len(c2.prices) == 0

    assert len(s.values) == 0
    assert len(c1.values) == 0
    assert len(c2.values) == 0


def test_strategybase_tree_adjust():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    s.adjust(1000)

    assert s.capital == 1000
    assert s.value == 1000
    assert c1.value == 0
    assert c2.value == 0
    assert c1.weight == 0
    assert c2.weight == 0


def test_strategybase_tree_update():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    i = 0
    s.update(dts[i], data.ix[dts[i]])

    c1.price == 100
    c2.price == 100

    i = 1
    s.update(dts[i], data.ix[dts[i]])

    c1.price == 105
    c2.price == 95

    i = 2
    s.update(dts[i], data.ix[dts[i]])

    c1.price == 100
    c2.price == 100


def test_strategybase_tree_allocate():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    i = 0
    s.update(dts[i], data.ix[dts[i]])

    s.adjust(1000)
    # since children have w == 0 this should stay in s
    s.allocate(1000)

    assert s.value == 1000
    assert s.capital == 1000
    assert c1.value == 0
    assert c2.value == 0

    # now allocate directly to child
    c1.allocate(500)

    assert c1.position == 5
    assert c1.value == 500
    assert s.capital == 1000 - 501
    assert s.value == 999
    assert c1.weight == 500.0 / 999
    assert c2.weight == 0


def test_strategybase_tree_allocate_level2():
    c1 = SecurityBase('c1')
    c12 = copy.deepcopy(c1)
    c2 = SecurityBase('c2')
    c22 = copy.deepcopy(c2)
    s1 = StrategyBase('s1', [c1, c2])
    s2 = StrategyBase('s2', [c12, c22])
    m = StrategyBase('m', [s1, s2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    m.setup(dts)

    i = 0
    m.update(dts[i], data.ix[dts[i]])

    m.adjust(1000)
    # since children have w == 0 this should stay in s
    m.allocate(1000)

    assert m.value == 1000
    assert m.capital == 1000
    assert s1.value == 0
    assert s2.value == 0
    assert c1.value == 0
    assert c2.value == 0

    # now allocate directly to child
    s1.allocate(500)

    assert s1.value == 500
    assert m.capital == 1000 - 500
    assert m.value == 1000
    assert s1.weight == 500.0 / 1000
    assert s2.weight == 0

    # now allocate directly to child of child
    c1.allocate(200)

    assert s1.value == 499
    assert s1.capital == 500 - 201
    assert c1.value == 200
    assert c1.weight == 200.0 / 499
    assert c1.position == 2

    assert m.capital == 1000 - 500
    assert m.value == 999
    assert s1.weight == 499.0 / 999
    assert s2.weight == 0

    assert c12.value == 0


def test_strategybase_tree_allocate_long_short():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    i = 0
    s.update(dts[i], data.ix[dts[i]])

    s.adjust(1000)
    c1.allocate(500)

    assert c1.position == 5
    assert c1.value == 500
    assert c1.weight == 500.0 / 999
    assert s.capital == 1000 - 501
    assert s.value == 999

    c1.allocate(-200)

    assert c1.position == 3
    assert c1.value == 300
    assert c1.weight == 300.0 / 998
    assert s.capital == 1000 - 501 + 199
    assert s.value == 998

    c1.allocate(-400)

    assert c1.position == -1
    assert c1.value == -100
    assert c1.weight == -100.0 / 997
    assert s.capital == 1000 - 501 + 199 + 399
    assert s.value == 997

    # close up
    c1.allocate(-c1.value)

    assert c1.position == 0
    assert c1.value == 0
    assert c1.weight == 0
    assert s.capital == 1000 - 501 + 199 + 399 - 101
    assert s.value == 996


def test_strategybase_tree_allocate_update():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = StrategyBase('p', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[1]] = 105
    data['c2'][dts[1]] = 95

    s.setup(dts)

    i = 0
    s.update(dts[i], data.ix[dts[i]])
    assert s.price == 100

    s.adjust(1000)

    assert s.price == 100

    c1.allocate(500)

    assert c1.position == 5
    assert c1.value == 500
    assert c1.weight == 500.0 / 999
    assert s.capital == 1000 - 501
    assert s.value == 999
    assert s.price == 99.9

    i = 1
    s.update(dts[i], data.ix[dts[i]])

    assert c1.position == 5
    assert c1.value == 525
    assert c1.weight == 525.0 / 1024
    assert s.capital == 1000 - 501
    assert s.value == 1024
    assert s.price == 102.4


def test_strategy_universe():
    s = Strategy('s')

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[0]] = 105
    data['c2'][dts[0]] = 95

    s.setup(data)

    i = 0
    s.update(dts[i])

    assert len(s.universe) == 1
    assert 'c1' in s.universe
    assert 'c2' in s.universe
    assert s.universe['c1'][dts[i]] == 105
    assert s.universe['c2'][dts[i]] == 95

    # should not have children unless allocated
    assert len(s.children) == 0


def test_strategy_allocate():
    s = Strategy('s')

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)
    data['c1'][dts[0]] = 100
    data['c2'][dts[0]] = 95

    s.setup(data)

    i = 0
    s.update(dts[i])

    s.adjust(1000)
    s.allocate('c1', 100)
    c1 = s['c1']

    assert c1.position == 1
    assert c1.value == 100
    assert s.value == 999


def test_strategy_close():
    s = Strategy('s')

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)

    s.setup(data)

    i = 0
    s.update(dts[i])

    s.adjust(1000)
    s.allocate('c1', 100)
    c1 = s['c1']

    assert c1.position == 1
    assert c1.value == 100
    assert s.value == 999

    s.close('c1')

    assert c1.position == 0
    assert c1.value == 0
    assert s.value == 998


def test_strategy_flatten():
    s = Strategy('s')

    dts = pd.date_range('2010-01-01', periods=3)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)

    s.setup(data)

    i = 0
    s.update(dts[i])

    s.adjust(1000)
    s.allocate('c1', 100)
    c1 = s['c1']
    s.allocate('c2', 100)
    c2 = s['c2']

    assert c1.position == 1
    assert c1.value == 100
    assert c2.position == 1
    assert c2.value == 100
    assert s.value == 998

    s.flatten()

    assert c1.position == 0
    assert c1.value == 0
    assert s.value == 996


def test_strategy_multiple_calls():
    s = Strategy('s')

    dts = pd.date_range('2010-01-01', periods=5)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)

    data.c2[dts[0]] = 95
    data.c1[dts[1]] = 95
    data.c2[dts[2]] = 95
    data.c2[dts[3]] = 95
    data.c2[dts[4]] = 95
    data.c1[dts[4]] = 105

    s.setup(data)

    # define strategy logic
    def algo(target):
        # close out any open positions
        target.flatten()

        # get stock w/ lowest price
        c = target.universe.ix[target.now].idxmin()

        # allocate all capital to that stock
        target.allocate(c, target.value)

    # replace run logic
    s.run = algo

    # start w/ 1000
    s.adjust(1000)

    # loop through dates manually
    i = 0

    # update t0
    s.update(dts[i])

    assert len(s.children) == 0
    assert s.value == 1000

    # run t0
    s.run(s)

    assert len(s.children) == 1
    assert s.value == 999
    assert s.capital == 49

    c2 = s['c2']
    assert c2.value == 950
    assert c2.weight == 950.0 / 999
    assert c2.price == 95

    # update out t0
    s.update(dts[i])

    c2 == s['c2']
    assert len(s.children) == 1
    assert s.value == 999
    assert s.capital == 49

    assert c2.value == 950
    assert c2.weight == 950.0 / 999
    assert c2.price == 95

    # update t1
    i = 1
    s.update(dts[i])

    assert s.value == 1049
    assert s.capital == 49
    assert len(s.children) == 1

    assert 'c2' in s.children
    c2 == s['c2']
    assert c2.value == 1000
    assert c2.weight == 1000.0 / 1049.0
    assert c2.price == 100

    # run t1 - close out c2, open c1
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1047
    assert s.capital == 2

    c1 = s['c1']
    assert c1.value == 1045
    assert c1.weight == 1045.0 / 1047
    assert c1.price == 95

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 100

    # update out t1
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1047
    assert s.capital == 2

    assert c1 == s['c1']
    assert c1.value == 1045
    assert c1.weight == 1045.0 / 1047
    assert c1.price == 95

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 100

    # update t2
    i = 2
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1102
    assert s.capital == 2

    assert c1.value == 1100
    assert c1.weight == 1100.0 / 1102
    assert c1.price == 100

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 95

    # run t2
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # update out t2
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # update t3
    i = 3
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # run t3
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # update out t3
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # update t4
    i = 4
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    # accessing price should refresh - this child has been idle for a while -
    # must make sure we can still have a fresh prices
    assert c1.price == 105
    assert len(c1.prices) == 5

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # run t4
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1096
    assert s.capital == 51

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 105

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1096
    assert c2.price == 95

    # update out t4
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1096
    assert s.capital == 51

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 105

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1096
    assert c2.price == 95


def test_strategy_multiple_calls_preset_secs():
    c1 = SecurityBase('c1')
    c2 = SecurityBase('c2')
    s = Strategy('s', [c1, c2])

    dts = pd.date_range('2010-01-01', periods=5)
    data = pd.DataFrame(index=dts, columns=['c1', 'c2'], data=100)

    data.c2[dts[0]] = 95
    data.c1[dts[1]] = 95
    data.c2[dts[2]] = 95
    data.c2[dts[3]] = 95
    data.c2[dts[4]] = 95
    data.c1[dts[4]] = 105

    s.setup(data)
    c1.setup(dts, data.c1)
    c2.setup(dts, data.c2)

    # define strategy logic
    def algo(target):
        # close out any open positions
        target.flatten()

        # get stock w/ lowest price
        c = target.universe.ix[target.now].idxmin()

        # allocate all capital to that stock
        target.allocate(c, target.value)

    # replace run logic
    s.run = algo

    # start w/ 1000
    s.adjust(1000)

    # loop through dates manually
    i = 0

    # update t0
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1000

    # run t0
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 999
    assert s.capital == 49

    assert c2.value == 950
    assert c2.weight == 950.0 / 999
    assert c2.price == 95

    # update out t0
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 999
    assert s.capital == 49

    assert c2.value == 950
    assert c2.weight == 950.0 / 999
    assert c2.price == 95

    # update t1
    i = 1
    s.update(dts[i])

    assert s.value == 1049
    assert s.capital == 49
    assert len(s.children) == 2

    assert c2.value == 1000
    assert c2.weight == 1000.0 / 1049.0
    assert c2.price == 100

    #assert c1.price == 95

    # run t1 - close out c2, open c1
    s.run(s)

    print c1.value
    assert c1.value == 1045
    assert c1.weight == 1045.0 / 1047
    assert c1.price == 95

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 100

    assert len(s.children) == 2
    assert s.value == 1047
    assert s.capital == 2

    # update out t1
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1047
    assert s.capital == 2

    assert c1.value == 1045
    assert c1.weight == 1045.0 / 1047
    assert c1.price == 95

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 100

    # update t2
    i = 2
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1102
    assert s.capital == 2

    assert c1.value == 1100
    assert c1.weight == 1100.0 / 1102
    assert c1.price == 100

    assert c2.value == 0
    assert c2.weight == 0
    assert c2.price == 95

    # run t2
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # update out t2
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # update t3
    i = 3
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1100
    assert s.capital == 55

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1100
    assert c2.price == 95

    # run t3
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # update out t3
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 100

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # update t4
    i = 4
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1098
    assert s.capital == 53

    assert c1.value == 0
    assert c1.weight == 0
    # accessing price should refresh - this child has been idle for a while -
    # must make sure we can still have a fresh prices
    assert c1.price == 105
    assert len(c1.prices) == 5

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1098
    assert c2.price == 95

    # run t4
    s.run(s)

    assert len(s.children) == 2
    assert s.value == 1096
    assert s.capital == 51

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 105

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1096
    assert c2.price == 95

    # update out t4
    s.update(dts[i])

    assert len(s.children) == 2
    assert s.value == 1096
    assert s.capital == 51

    assert c1.value == 0
    assert c1.weight == 0
    assert c1.price == 105

    assert c2.value == 1045
    assert c2.weight == 1045.0 / 1096
    assert c2.price == 95