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
        inserter = backend.BulkInserter(collection, threshold=10, unique_attr='value')
        for doc in documents:
            inserter.insert(doc)
        # we should have inserted 10 documents, with 5 hanging around
        self.assertEquals(collection.find().count(), 10)
        self.assertEquals(inserter.total, 5)
        self.assertEquals(inserter._inserts, 10)
        inserter.flush()
        self.assertEquals(collection.find().count(), 15)
        self.assertEquals(inserter.total, 0)
        self.assertEquals(inserter._inserts, 15)
        # this time, they should be updates, even though they 'look' like inserts
        documents = [{'value': str(i), 'foo': 'bar'} for i in xrange(1, 15+1)]
        for doc in documents:
            inserter.insert(doc)
        # here, we're updating documents with some changes to them; the inserts
        # would fail silently if they were tried with documents that had _ids,
        # and the collection would grow if these were not updates
        self.assertEquals(collection.find({'foo': 'bar'}).count(), 10)
        inserter.flush()
        self.assertEquals(collection.find({'foo': 'bar'}).count(), 15)
        self.assertEquals(collection.find().count(), 15)
        self.assertEquals(inserter._inserts, 15)
        self.assertEquals(inserter._updates, 15)

    def test_mixed_insertion(self):
        collection = self.db[self.collection]
        self._collision_setup()
        documents = [{'value': str(i), 'foo': 'bar'} for i in xrange(1, 200+1)]
        inserter = backend.BulkInserter(collection, threshold=50, unique_attr='value')
        inserter.insert(*documents)
        self.assertEquals(inserter._updates, 100)
        self.assertEquals(inserter._inserts, 100)
        self.assertEquals(collection.find({'foo':'bar'}).count(), 200)

class PagerTest(TestCase):
    def __init__(self, *args):
        super(PagerTest, self).__init__(*args)
        self.db = backend.get_database()
        self.collection = 'PagerTest'

    def setUp(self):
        collection = self.db[self.collection]
        collection.insert([{'value': i} for i in xrange(1, 2500+1)])

    def tearDown(self):
        self.db.drop_collection(self.collection)

    def test_paging_cursor(self):
        collection = self.db[self.collection]
        cursor = backend.Pager(collection, threshold=250)
        items = cursor.find({'value': {'$lte' : 1500}})
        # make sure that when we iterate over it, it only ever has 'threshold'
        for item in items:
            self.assertEquals(len(items._page), 250)
        self.assertEquals(items._num_pages, 6)
        # first, make sure that using it behaves regularly
        items = cursor.find({'value': {'$lte' : 1500}})
        item_list = list(items)
        self.assertEquals(len(item_list), 1500)


