#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Backend data helpers for iris.

Iris uses mongodb because it's web scale."""

import os
import imghdr

import pymongo
import threading

from iris.loaders import file, picasa
from iris.utils import memoize, OpenStruct, exclude_self

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
    return db

def flush():
    """Flush the iris database.  You should probably only do this if you're
    testing things."""
    db = get_database()
    db.drop_collection('photos')

class BulkInserter(object):
    """A caching updater for mongo documents going into the same collection.
    You can choose a threshold, and add documents to it, and they will be
    flushed after the threshold number of documents have been reached."""
    def __init__(self, collection, threshold=100, unique_attr=None):
        # this has to be reentrant so we can protect flushes
        self.collection = collection
        self.unique_attr = unique_attr
        self.threshold = threshold
        self.total = 0
        self.documents = {
            'updates' : [],
            'inserts' : [],
        }
        self._inserts = 0
        self._updates = 0
        self.lock = threading.RLock()

    def insert(self, *documents):
        """Add one or more documents to be updated whenever the threshold is met.
        If the document has an '_id', it's considered an update.  If it doesn't,
        it's considered an insert.  If the document has a '_unique_attr'
        attribute, it's used later to check if it is actually an insert or an
        update.  This method is thread safe."""
        self.lock.acquire()
        for document in documents:
            document = dict(document)
            if '_id' in document:
                self.documents['updates'].append(document)
            else:
                self.documents['inserts'].append(document)
            self.total += 1
            if self.total >= self.threshold:
                self.flush(False)
        self.lock.release()

    def flush(self, force=True):
        """Flush all of the documents with as few queries as possible.  If
        force is False (default), documents are only saved if they meet the
        threshold.  This method is thread safe."""
        self.lock.acquire()
        if self.total < self.threshold and not force:
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
        updates = self.documents['updates']
        inserts = self.documents['inserts']
        lookups = {}
        # check all insert documents for a 'unique attr' that will allow us
        # to search the db for possible duplicates
        for document in inserts:
            unique = getattr(document, '_unique_attr', self.unique_attr)
            if unique:
                lookups.setdefault(unique, {})[document[unique]] = document
        # search db for duplicates based on unique attrs of insert documents
        results = {}
        for lookup,values in lookups.iteritems():
            keys = [lookup]
            if '_id' not in keys:
                keys.append('_id')
            spec = {lookup: {'$in' : list(values)}}
            results[lookup] = dict([(d[lookup], d['_id']) for d in self.collection.find(spec, keys)])
        # for each match, remove that document from inserts, add the _id from
        # the database, and add that document to updates
        for key in results:
            for unique, _id in results[key].iteritems():
                # add _id to document in inserts with unique value 'unique'
                document = lookups[key][unique]
                # XXX: this is O(n) but it could be O(1);  room for improvement
                # here with potentially large docucment cache thresholds
                inserts.remove(document)
                document['_id'] = _id
                updates.append(document)
        if inserts:
            self.collection.insert(inserts)
        for doc in updates:
            self.collection.save(doc)
        self._clear()

    def _clear(self):
        """Clears out documents that have already been flushed.  This method
        is NOT thread safe."""
        self._inserts += len(self.documents['inserts'])
        self._updates += len(self.documents['updates'])
        self.documents.clear()
        self.documents['updates'] = []
        self.documents['inserts'] = []
        self.total = 0

class PagingCursor(object):
    """A cursor-like object that iterates through a large queryset a little at
    a time.  Meant to be used by the Pager only, its behavior is determined by
    the Pager that created it.  It is NOT thread safe to iterate a PagingCursor
    from multiple threads, as it uses internal state to store pagination."""
    def __init__(self, pager, *args, **kwargs):
        self.__dict__.update(exclude_self(locals()))
        self.collection = pager.collection
        self.threshold = pager.threshold
        # we need a stable sort in order to page reliably
        self._sort = kwargs.get('sort', pager.sort)
        # adjust for a base skip
        self._base_skip = kwargs.get('skip', 0)
        # adjust for a given limit
        self._base_limit = kwargs.get('limit', None)
        self._num_pages = 0
        self._page = []

    def _next_query(self):
        skip = self._base_skip + (self._num_pages * self.threshold)
        limit = self.threshold
        if self._base_limit is not None:
            distance = (skip - self._base_skip) + limit
            if distance > self._base_limit:
                limit = (self._base_skip + self._base_limit) - skip
            if skip == (self._base_skip + self._base_limit):
                self._page = []
                return
        assert limit >= 0
        kwargs = dict(self.kwargs)
        kwargs['skip'] = skip
        kwargs['limit'] = limit
        kwargs['sort'] = self._sort
        self._page = list(self.collection.find(*self.args, **kwargs))
        if self._page:
            self._num_pages += 1

    def __iter__(self):
        self._next_query()
        while self._page:
            for item in self._page:
                yield item
            self._next_query()

class Pager(object):
    """A class that can perform simple 'finds' against a database and present
    one iterate over all results even though only a maximum of `threshold`
    (default: 100) are ever loaded at one time."""
    def __init__(self, collection, sort=None, threshold=100):
        self.collection = collection
        self.threshold = threshold
        self.sort = sort or [('_id', pymongo.DESCENDING)]

    def find(self, *args, **kwargs):
        return PagingCursor(self, *args, **kwargs)

class Model(OpenStruct):
    """A base model for whatever types of data we need to save.  For now this
    is just photos, but we might have some more application data to save."""
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

class Manager(object):
    """A thin wrapper around a generic mongo collection cursor that auto-applies
    our class and """
    def __init__(self, cls):
        self.cls = cls
        try:
            self.collection = get_database()[cls._collection]
        except:
            self.collection = None

    def _init(self):
        if self.collection is None:
            self.collection = get_database()[self.cls._collection]

    def find(self, *args, **kwargs):
        self._init()
        if 'as_class' not in kwargs:
            kwargs['as_class'] = self.cls
        if 'paged' in kwargs:
            pager = Pager(self.collection, threshold=kwargs['paged'])
            return pager.find(*args, **kwargs)
        return self.collection.find(*args, **kwargs)

class Photo(Model):
    _collection = 'photos'

    def load_file(self, path):
        path = os.path.realpath(path)
        meta = file.MetaData(path)
        copykeys = ('x', 'y', 'exif', 'iptc', 'tags', 'path', 'caption')
        d = dict([(k,v) for k,v in meta.__dict__.iteritems() if k in copykeys])
        self.__dict__.update(d)
        stat = os.stat(meta.path)
        self.size = stat.st_size

    def __repr__(self):
        return '<iris.backend.Photo "%s">' % (self.path or self._id or '(at 0x%08X)' % id(self))

# XXX: we could do this in a meta class but for now this is fine
Photo.objects = Manager(Photo)

