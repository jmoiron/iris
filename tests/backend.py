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
        """A simple set of tests that makes sure our paging cursor functions
        properly on simple queries."""
        collection = self.db[self.collection]
        cursor = backend.Pager(collection, threshold=250)
        items = cursor.find({'value': {'$lte' : 1500}})
        for item in items:
            self.assertEquals(len(items._page), 250)
        self.assertEquals(items._num_pages, 6)
        items = cursor.find({'value': {'$lte' : 1500}})
        item_list = list(items)
        self.assertEquals(len(item_list), 1500)
        items = cursor.find({'value': {'$lte' : 371}})
        item_list = list(items)
        self.assertEquals(len(item_list), 371)
        self.assertEquals(items._num_pages, 2)

    def test_paging_cursor_values(self):
        """Test that the paging cursor allows us to restrict values in returned
        documents like the regular 'find'."""
        collection = self.db[self.collection]
        cursor = backend.Pager(collection, threshold=100)
        items = cursor.find({'value': {'$lte' : 500}}, ['_id'])
        for item in items:
            self.assertEquals(len(item.keys()), 1)
            self.assertEquals(item.keys()[0], '_id')
        self.assertEquals(items._num_pages, 5)

    def test_paging_cursor_sort(self):
        """Test that the paging cursor allows a custom sort."""
        import pymongo
        collection = self.db[self.collection]
        cursor = backend.Pager(collection, threshold=100)
        items = cursor.find({'value': {'$lte' : 500}}, sort=[('value', pymongo.ASCENDING)])
        item_list = list(items)
        self.assertEquals(item_list[0]['value'], 1)
        self.assertEquals(item_list[-1]['value'], 500)
        self.assertEquals(items._num_pages, 5)
        items = cursor.find({'value': {'$lte' : 600}}, sort=[('value', pymongo.DESCENDING)])
        item_list = list(items)
        self.assertEquals(item_list[0]['value'], 600)
        self.assertEquals(item_list[-1]['value'], 1)
        self.assertEquals(items._num_pages, 6)

    def test_paging_cursor_skip_limit(self):
        """Test that the paging cursor allows transparent handling of custom
        skip/limit settings."""
        collection = self.db[self.collection]
        cursor = backend.Pager(collection, threshold=100)
        # this should only go through 2 pages, from 500 - 1000
        items = cursor.find({'value': {'$lte': 1500}}, skip=500, limit=500)
        item_list = list(items)
        self.assertEquals(items._num_pages, 5)
        self.assertEquals(item_list[0]['value'], 1000)
        self.assertEquals(item_list[-1]['value'], 501)

