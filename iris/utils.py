#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" """

import os
from functools import wraps
import math
import multiprocessing

# terminal color rubbish
white,black,red,green,yellow,blue,purple = range(89,96)
def color(string, color=green, bold=False):
    return '\033[%s%sm' % ('01;' if bold else '', color) + str(string) + '\033[0m'

def bold(string, color=white):
    return globals()['color'](string, color, True)

def error(string):
    print color('Error: ', red, True) + str(string)

# the following code is from my gist here:
#   http://gist.github.com/596073
def split(iterable, n):
    """Splits an iterable up into n roughly equally sized groups."""
    groupsize = int(math.floor(len(iterable) / float(n)))
    remainder = len(iterable) % n
    sizes = [groupsize+1 for i in range(remainder)] + [groupsize]*(n-remainder)
    pivot, groups = 0, []
    for size in sizes:
        groups.append(iterable[pivot:pivot+size])
        pivot += size
    return groups

def parallelize(n, function, args):
    """Parallelizes a function n ways.  Returns a list of results.  The
    function must be one that takes a list of arguments and operates over
    them all, with each item dealt with in isolation from the others."""
    pool = multiprocessing.Pool(n)
    arg_groups = split(args, n)
    waiters = []
    for i in range(n):
        waiters.append(
            pool.apply_async(function, (arg_groups[i],))
        )
    results = [r.get() for r in waiters]
    return results

def auto_parallelize(function, args):
    """Auto-parallelizes a function depending on the number of cpu cores."""
    n = multiprocessing.cpu_count()
    return parallelize(n, function, args)

# returns all paths to filenames under a list of paths
def recursive_walk(*paths):
    ignore = set(['.git', '.svn', '.hg'])
    visited_files = set()
    visited_dirs = set()
    for path in paths:
        if os.path.isdir(path):
            visited_dirs.add(path)
            for root, dirs, files in os.walk(path):
                pruned = []
                for directory in dirs:
                    d = os.path.join(root, directory)
                    if d in visited_dirs:
                        pruned.append(directory)
                    if d in ignore:
                        pruned.append(directory)
                for d in pruned:
                    dirs.remove(d)
                for f in files:
                    visited_files.add(os.path.join(root, f))
        elif os.path.isfile(path):
            visited_files.add(path)
    return sorted(list(visited_files))

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

