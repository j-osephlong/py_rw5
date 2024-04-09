import pytest

from py_rw5.parse.dms import DMS


def test_from_str():
    dms_str = "30.1550"

    dms = DMS.from_str(dms_str)

    assert dms.degrees == 30
    assert dms.minutes == 15
    assert dms.seconds == 50


def test_str_repr():
    dms = DMS(30, 15, 50)
    assert str(dms) == "30-15-50.00"

    dms = DMS(1, 15, 00)
    assert str(dms) == "1-15-00.00"

    dms = DMS(312, 15, 1.1)
    assert str(dms) == "312-15-01.10"


def test_decimal_degrees():
    dms = DMS(30, 15, 50)

    assert (dms.dd - 30.26388) < 0.00001


def test_from_degrees():
    decimal_degrees = 30.263888889

    dms = DMS.from_degrees(decimal_degrees)

    assert dms.degrees == 30
    assert dms.minutes == 15
    assert dms.seconds == 50

    assert (dms.dd - decimal_degrees) < 0.00001


def test_subtraction():
    a = DMS(45, 34, 56)
    b = DMS(25, 45, 39)

    c = a - b

    assert c.degrees == 19
    assert c.minutes == 49
    assert c.seconds == 17


def test_equals():
    a = DMS(45, 34, 56)
    b = DMS(25, 45, 39)
    c = DMS(25, 45, 39)

    assert a != b
    assert a != c
    assert b == c
    assert c == b
