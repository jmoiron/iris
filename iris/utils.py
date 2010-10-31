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

class OpenStruct(object):
    """Ruby style openstruct.  Implemented by myself millions of times."""
    def __init__(self, *d, **dd):
        if d and not dd:
            self.__dict__.update(d[0])
        else:
            self.__dict__.update(dd)
    def __iter__(self):  return iter(self.__dict__)
    def __getattr__(self, attr): return self.__getitem__(attr)
    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            return None
    def __setitem__(self, item, value): self.__dict__[item] = value
    def __delitem__(self, item):
        if item in self.__dict__:
            del self.__dict__[item]
    # the rest of the dict interface
    def get(self, key, *args):
        return self.__dict__.get(key, *args)
    def keys(self):  return self.__dict__.keys()
    def iterkeys(self): return self.__dict__.iterkeys()
    def values(self): return self.__dict__.values()
    def itervalues(self): return self.__dict__.itervalues()
    def items(self): return self.__dict__.items()
    def iteritems(self): return self.__dict__.iteritems()
    def update(self, d): self.__dict__.update(d)
    def clear(self): self.__dict__.clear()

