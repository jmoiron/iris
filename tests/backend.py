#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""iris backend tests."""

from unittest import TestCase
from iris import backend

class BulkInserterTest(TestCase):
    def __init__(self, *args):
        super(BulkInserterTest, self).__init__(*args)
        self.db = backend.get_database()
        self.collection = 'BulkInserterTest'

    def tearDown(self):
        self.db.drop_collection(self.collection)

    def _collision_setup(self):
        collection = self.db[self.collection]
        documents = [{'value': str(i)} for i in xrange(1, 200+1, 2)]
        collection.insert(documents)

    def test_normal_insertion(self):
        collection = self.db[self.collection]
        documents = [{'value': str(i)} for i in xrange(1, 15+1)]
        updater = backend.BulkInserter(collection, threshold=10, unique_attr='value')
        for doc in documents:
            updater.update(doc)
        # we should have inserted 10 documents, with 5 hanging around
        self.assertEquals(collection.find().count(), 10)
        self.assertEquals(updater.total, 5)
        self.assertEquals(updater._inserts, 10)
        updater.flush()
        self.assertEquals(collection.find().count(), 15)
        self.assertEquals(updater.total, 0)
        self.assertEquals(updater._inserts, 15)
        # this time, they should be updates, even though they 'look' like inserts
        documents = [{'value': str(i), 'foo': 'bar'} for i in xrange(1, 15+1)]
        for doc in documents:
            updater.update(doc)
        # here, we're updating documents with some changes to them; the inserts
        # would fail silently if they were tried with documents that had _ids,
        # and the collection would grow if these were not updates
        self.assertEquals(collection.find({'foo': 'bar'}).count(), 10)
        updater.flush()
        self.assertEquals(collection.find({'foo': 'bar'}).count(), 15)
        self.assertEquals(collection.find().count(), 15)
        self.assertEquals(updater._inserts, 15)
        self.assertEquals(updater._updates, 15)

    def test_mixed_insertion(self):
        collection = self.db[self.collection]
        self._collision_setup()
        documents = [{'value': str(i), 'foo': 'bar'} for i in xrange(1, 200+1)]
        updater = backend.BulkInserter(collection, threshold=50, unique_attr='value')
        updater.update(*documents)
        self.assertEquals(updater._updates, 100)
        self.assertEquals(updater._inserts, 100)
        self.assertEquals(collection.find({'foo':'bar'}).count(), 200)


