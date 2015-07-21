# -*- coding: utf-8 -*-
'''
Utilities for writing threaded applications with click:

- There is a global ``ctx`` object to be used.

- The ``click`` object's attributes are supposed to be used instead of the
  click package's content.

  - It wraps some UI functions such that they don't produce overlapping
    output or prompt the user at the same time.

  - It wraps BaseCommand subclasses such that their invocation changes the
    ctx global, and also changes the shortcut decorators to use the new
    classes.
'''

import functools
import threading


class _ClickProxy(object):
    def __init__(self, wrappers, click=None):
        if click is None:
            import click
        self._click = click
        self._cache = {}
        self._wrappers = dict(wrappers)

    def __getattr__(self, name):
        if name not in self._cache:
            f = getattr(self._click, name)
            f = self._wrappers.get(name, lambda x: x)(f)
            self._cache[name] = f

        return self._cache[name]


_ui_lock = threading.Lock()


def _ui_function(f):
    @functools.wraps(f)
    def inner(*a, **kw):
        with _ui_lock:
            rv = f(*a, **kw)
        return rv
    return inner


WRAPPERS = {
    'echo': _ui_function,
    'echo_via_pager': _ui_function,
    'prompt': _ui_function,
    'confirm': _ui_function,
    'clear': _ui_function,
    'edit': _ui_function,
    'launch': _ui_function,
    'getchar': _ui_function,
    'pause': _ui_function,
}

click = _ClickProxy(WRAPPERS)
