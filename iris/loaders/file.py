#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""EXIF Loaders for files."""

import datetime

import pyexiv2
if pyexiv2.version_info < (0, 3, 0):
    from pyexiv2.utils import Rational, GPSCoordinate
    Fraction = type
    examine_types = (Rational, GPSCoordinate, list, datetime.date, datetime.time)
else:
    from pyexiv2.utils import Rational, GPSCoordinate, Fraction
    examine_types = (Rational, GPSCoordinate, list, datetime.date, datetime.time, Fraction)

from iris import utils

def time_format(time):
    return '%02d:%02d:%02d' % (time.hour, time.minute, time.second)

def date_format(date):
    return datetime.datetime(date.year, date.month, date.day)

def exiv_serialize(key, value):
    """EXIF saves a lot of data as fractions.  We want to smartly undo
    that where it makes sense, or to a string "num/denom" where that
    makes sense."""
    if not isinstance(value, examine_types):
        if isinstance(value, basestring) and '\x00' in value:
            return '(bin)'
        return value
    if isinstance(value, list):
        return [exiv_serialize(key, v) for v in value]
    elif isinstance(value, datetime.time):
        if not value.tzinfo:
            return time_format(value)
        h,m,s = value.hour, value.minute, value.second
        seconds = h * 3600 + m * 60 + s
        adjusted = seconds + (value.tzinfo.utcoffset(value).seconds)
        if 0 <= adjusted <= 86400:
            time = datetime.time(adjusted/3600, (adjusted % 3600)/60, adjusted % 60)
            return time_format(time)
        utils.warn('timezone on timestamp adjusts date when converted to UTC.')
        return time_format(datetime.time(h,m,s))
    elif isinstance(value, datetime.date):
        return date_format(value)

    fraction_keys = []
    float_keys = {
        'ApertureValue' : '%0.1f',
        'FNumber' : '%0.1f',
    }

    if key in fraction_keys or isinstance(value, Fraction):
        return "%s/%s" % (value.numerator, value.denominator)
    if key in float_keys:
        format = float_keys[key]
        return format % value.to_float()
    if value.denominator > 4096:
        return '%0.2f' % value.to_float()
    return '%s/%s' % (value.numerator, value.denominator)

def extract_tags(exif, iptc):
    """Given exif and iptc data, try to extract tags from them."""
    tags = iptc.get('Application2', {}).get('Keywords', [])
    tags += iptc.get('Application', {}).get('Keywords', [])
    return tags

def extract_caption(exif, iptc):
    """Given exif and iptc table, try to extract a caption."""
    caption = iptc.get('Application2', {}).get('Caption', '')
    return caption or None

def discard(key):
    return key.startswith('0x')

class UnknownImageTypeException(Exception):
    pass

class MetaData(object):
    """Encapsulation of image metadata.  Accessing the 'exif' or 'iptc'
    attributes will get you a hierarchical dictionary with the correct
    types.  Accessing 'metas' will get you a combined dictionary, with
    exif rooted at 'Exif' and iptc rooted at 'Iptc'."""

    def __init__(self, path):
        _metadata = pyexiv2.ImageMetadata(path)
        UITException = UnknownImageTypeException('File at `%s` mangled or of unknown type (not an image?)' % path)
        try:
            _metadata.read()
        except IOError:
            raise UITException
        self._metadata = _metadata
        x,y = _metadata.dimensions
        # XXX: Canon Movie Thumbnails (.THM) seem to have valid EXIF metadata,
        # but then choke the actual exif parser;  we should just ignore.
        try:
            exif = self._exif()
        except pyexiv2.exif.ExifValueError:
            raise UITException
        iptc = self._iptc()
        tags = extract_tags(exif, iptc)
        caption = extract_caption(exif, iptc)
        self.__dict__.update(utils.exclude_self(locals()))

    def metas(self):
        return {
            'exif' : self.exif(),
            'iptc' : self.iptc(),
        }

    def _hierarchical_split(self, keys):
        m = self._metadata
        d = {}
        for key in keys:
            parts = key.split('.')[1:]
            cur = d
            for part in parts[:-1]:
                cur.setdefault(part, {})
                cur = cur[part]
            name = parts[-1]
            if discard(name):
                continue
            if key.startswith('Iptc'):
                cur[name] = exiv_serialize(name, m[key].values)
            else:
                cur[name] = exiv_serialize(name, m[key].value)
        return d

    def _exif(self):
        return self._hierarchical_split(self._metadata.exif_keys)

    def _iptc(self):
        return self._hierarchical_split(self._metadata.iptc_keys)



