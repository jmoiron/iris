#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Backend data helpers for iris.

Iris uses mongodb because it's web scale."""

import os
import imghdr

import pymongo

from iris.loaders import file, picasa
from iris.utils import memoize

@memoize
def get_database(host=None, port=None):
    """Get the iris mongo db from host and port.  If none are supplied, attempt
    to read an iris configuration file.  If it doesn't exist, connect to
    localhost:27017."""
    if host is None or port is None:
        from iris import config
        cfg = config.IrisConfig()
        try:
            cfg.read()
            host, port = cfg.host, cfg.port
        except:
            host, port = '127.0.0.1', 27017
    connection = pymongo.Connection(host, port)
    db = connection.iris
    photos = db.photos
    photos.create_index([('path', pymongo.DESCENDING)])
    photos.create_index([('date', pymongo.DESCENDING)])
    return connection.iris

class Photo(object):
    def __init__(self, path_or_dict):
        if isinstance(path_or_dict, basestring):
            self.load(path_or_dict)
        else:
            self._init_from_dict(path_or_dict)

    def load(self, path):
        path = os.path.realpath(path)
        meta = file.MetaData(path)
        copykeys = ('x', 'y', 'exif', 'iptc', 'tags', 'path')
        d = dict([(k,v) for k,v in meta.__dict__.iteritems() if k in copykeys])
        self.__dict__.update(d)
        stat = os.stat(meta.path)
        self.size = stat.st_size

    def _init_from_dict(self, d):
        """When loading from the db."""
        self.__dict__.update(d)

    def _save(self):
        import bson
        db = get_database()
        if not hasattr(self, '_id'):
            photo = db.photos.find_one({'path': self.path})
            if photo: self._id = photo['_id']
        value = dict(self.__dict__)
        try:
            db.photos.save(value)
        except bson.errors.InvalidDocument:
            import traceback
            tb = traceback.format_exc()
            import ipdb; ipdb.set_trace();

class FileLoader(object):
    pass

