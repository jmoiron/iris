#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Backend data helpers for iris.

Iris uses mongodb because it's web scale."""

import os
import imghdr

import pymongo
import threading

from iris.loaders import file, picasa
from iris.utils import memoize, OpenStruct

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

class BulkUpdater(object):
    """A caching updater for mongo documents going into the same collection.
    You can choose a threshold, and add documents to it, and they will be
    flushed after the threshold number of documents have been reached."""
    def __init__(self, collection, flush_threshold=100):
        # this has to be reentrant so we can protect flushes
        self.collection = collection
        self.lock = threading.RLock()
        self.flush_threshold = 100
        self.total = 0
        self.documents = {
            'updates' : [],
            'inserts' : [],
        }

    def update(self, document):
        """Add a document to be updated whenever the threshold is met.  If the
        document has an '_id', it's considered an update.  If it doesn't, it's
        considered an insert.  If the document has a '_unique_attr' attribute,
        it's used later to check if it is actually an insert or an update.
        This method is thread safe."""
        self.lock.acquire()
        if '_id' in document:
            self.documents['updates'].append(document)
        else:
            self.documnets['inserts'].append(document)
        self.total += 1
        if self.total >= self.total:
            self.flush()
        self.lock.release()

    def flush(self, force=False):
        """Flush all of the documents with as few queries as possible.  If
        force is False (default), documents are only saved if they meet the
        threshold.  This method is thread safe."""
        self.lock.acquire()
        if self.total < self.flush_threshold and not force:
            self.lock.release()
            return
        self._flush()
        self.lock.release()

    def _flush(self):
        """Save all documents with as few queries as possible.  Checks the
        db for 'inserts' documents that pre-exist (based on the presence of
        a '_unique_attr' attribute), and moves those that exist over to the
        'updates', then bulk inserts whatever's left and saves the others one
        at a time.  This method is NOT thread safe."""
        updates, inserts = self.documents['updates'], self.documents['inserts']
        lookups = {}
        for document in inserts:
            unique = getattr(document, '_unique_attr', None)
            if unique:
                lookups.setdefault(unique, []).append(document[unique])

class Model(OpenStruct):
    def save(self):
        import bson
        db = get_database()
        collection_name = getattr(self, '_collection', None)
        collection = db[collection_name]
        try:
            collection.save(self.__dict__)
        except bson.errors.InvalidDocument:
            import traceback
            tb = traceback.format_exc()
            import ipdb; ipdb.set_trace();


class Photo(Model):
    _collection = 'photos'

    def from_path(self, path):
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

    def sync(self):
        self.load(self.path)
        self.save()

class FileLoader(object):
    pass

