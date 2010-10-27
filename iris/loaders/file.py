#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""EXIF Loaders for files."""

import pyexiv2
from pyexiv2.utils import Rational, GPSCoordinate

from iris.utils import exclude_self, memoize

def exiv_serialize(key, value):
    """EXIF saves a lot of data as fractions.  We want to smartly undo
    that where it makes sense, or to a string "num/denom" where that
    makes sense."""
    if not isinstance(value, (Rational, GPSCoordinate)):
        return value

    fraction_keys = []
    float_keys = {'ApertureValue' : '%0.1f',}

    if key in fraction_keys:
        return "%s/%s" % (value.numerator, value.denominator)
    if key in float_keys:
        format = float_keys[key]
        return format % value.to_float()
    if value.denominator > 4096:
        return '%0.2f' % value.to_float()
    return '%s/%s' (value.numerator, value.denominator)

class MetaData(object):
    """Encapsulation of image metadata.  Accessing the 'exif' or 'iptc'
    attributes will get you a hierarchical dictionary with the correct
    types.  Accessing 'metas' will get you a combined dictionary, with
    exif rooted at 'Exif' and iptc rooted at 'Iptc'."""

    def __init__(self, path):
        _metadata = pyexiv2.ImageMetadata(path)
        _metadata.read()
        x,y = _metadata.dimensions
        self.__dict__.update(exclude_self(locals()))

    @memoize
    def metas(self):
        return = {
            'Exif' : self.exif(),
            'Iptc' : self.iptc(),
        }

    @memoize
    def exif(self):
        m = self._metadata
        d = {}
        for key in m.exif_keys:
            parts = key.split('.')
            if parts[0] == 'Exif':
                parts = parts[1:]
            cur = d
            for part in parts[:-1]:
                cur.setdefault(part, {})
                cur = cur[part]
            name = parts[-1]
            cur[name] = m[key].value
        return d

    @memoize
    def iptc(self):
        m = self._metadata
        d = {}
        for key in m.iptc_keys:
            import ipdb; ipdb.set_trace();
            parts = key.split('.')
            if parts[0] == 'IPTC':
                parts = parts[1:]
            cur = d
            for part in parts[:-1]:
                cur.setdefault(part, {})
                cur = cur[part]
            name = parts[-1]
            cur[name] = m[key].value
        return d
