#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" """

from functools import wraps

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

