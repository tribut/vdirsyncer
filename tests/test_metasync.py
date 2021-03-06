# -*- coding: utf-8 -*-

import pytest

from vdirsyncer.metasync import MetaSyncConflict, metasync
from vdirsyncer.storage.memory import MemoryStorage


def test_irrelevant_status():
    a = MemoryStorage()
    b = MemoryStorage()
    status = {'foo': 'bar'}

    metasync(a, b, status, keys=())
    assert not status


def test_basic():
    a = MemoryStorage()
    b = MemoryStorage()
    status = {}

    a.set_meta('foo', 'bar')
    metasync(a, b, status, keys=['foo'])
    assert a.get_meta('foo') == b.get_meta('foo') == 'bar'

    a.set_meta('foo', 'baz')
    metasync(a, b, status, keys=['foo'])
    assert a.get_meta('foo') == b.get_meta('foo') == 'baz'

    b.set_meta('foo', None)
    metasync(a, b, status, keys=['foo'])
    assert a.get_meta('foo') is b.get_meta('foo') is None


def test_conflict():
    a = MemoryStorage()
    b = MemoryStorage()
    status = {}
    a.set_meta('foo', 'bar')
    b.set_meta('foo', 'baz')

    with pytest.raises(MetaSyncConflict):
        metasync(a, b, status, keys=['foo'])

    assert a.get_meta('foo') == 'bar'
    assert b.get_meta('foo') == 'baz'
    assert not status


def test_conflict_same_content():
    a = MemoryStorage()
    b = MemoryStorage()
    status = {}
    a.set_meta('foo', 'bar')
    b.set_meta('foo', 'bar')

    metasync(a, b, status, keys=['foo'])
    assert a.get_meta('foo') == b.get_meta('foo') == status['foo'] == 'bar'


@pytest.mark.parametrize('wins', 'ab')
def test_conflict_x_wins(wins):
    a = MemoryStorage()
    b = MemoryStorage()
    status = {}
    a.set_meta('foo', 'bar')
    b.set_meta('foo', 'baz')

    metasync(a, b, status, keys=['foo'],
             conflict_resolution='a wins' if wins == 'a' else 'b wins')

    assert a.get_meta('foo') == b.get_meta('foo') == status['foo'] == (
        'bar' if wins == 'a' else 'baz'
    )
