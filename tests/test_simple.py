from exalt import promote, ShadowingConstantsError, UnsupportedCallableError

from pytest import raises

BAR = 10
BAR_1 = 1


def foo():
    return bar


def foo_with_consts():
    bar_1 = BAR_1
    return bar


def foo_closure_with_cell():
    bar = BAR

    def foo_closure():
        return bar

    return foo_closure


def foo_closure():
    def foo_closure():
        return bar

    return foo_closure


def foo_with_arg(bar_1):
    return bar, bar_1


def test_direct():
    assert promote(foo, bar=BAR)() == BAR


def test_wrong_order():
    assert promote(foo, bar_1=BAR_1, bar=BAR)() == BAR


def test_locals():
    bar = BAR
    assert promote(foo, **locals())() == BAR


def test_shadowing_const():
    with raises(ShadowingConstantsError) as e_info:
        promote(foo_with_consts, bar_1=BAR_1)()


def test_non_shadowing_const():
    promote(foo_with_consts, bar=BAR)()


def test_closure_with_cell():
    with raises(UnsupportedCallableError) as e_info:
        promote(foo_closure_with_cell(), bar=BAR)()


def test_closure():
    assert promote(foo_closure(), bar=BAR)() == BAR


def test_arg():
    assert promote(foo_with_arg, bar=BAR)(BAR_1) == (BAR, BAR_1)


def test_shadowing_arg():
    with raises(ShadowingConstantsError) as e_info:
        promote(foo_with_arg, bar_1=BAR_1)(BAR_1) == (BAR, BAR_1)
