#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" """

from functools import wraps

# terminal color rubbish
white,black,red,green,yellow,blue,purple = range(89,96)
def color(string, color=green, bold=False):
    return '\033[%s%sm' % ('01;' if bold else '', color) + str(string) + '\033[0m'

def bold(string, color=white):
    return globals()['color'](string, color, True)

def exclude_self(d):
    copy = dict(d)
    copy.pop('self', None)
    return copy

def memoize(function):
    _cache = {}
    @wraps(function)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in _cache:
            _cache[key] = function(*args, **kwargs)
        return _cache[key]
    return wrapper

def humansize(bytesize, persec=False):
    """Humanize size string for bytesize bytes."""
    units = ['Bps', 'KBps', 'MBps', 'GBps'] if persec else ['B', 'KB', 'MB', 'GB']
    # order of magnitude
    reduce_factor = 1024.0
    oom = 0 
    while bytesize /(reduce_factor**(oom+1)) >= 1:
        oom += 1
    return '%0.2f %s' % (bytesize/reduce_factor**oom, units[oom])

def error(string):
    print color('Error: ', red, True) + str(string)

