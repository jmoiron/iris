#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""iris query parser tests."""

from unittest import TestCase
from iris.query import parser as q

ME = q.FullFirstMatchException

class TokenTestCase(TestCase):
    """Like a regular TestCase, but with some extra asserts."""
    def assertToken(self, token, type, name=None):
        """Assert one token is of a type and, possibly, a value."""
        if type in(int, float, str, list):
            self.assertTrue(isinstance(token, type))
            if name:
                self.assertEquals(token, name)
        if type == 'field':
            self.assertEquals(token.type, 'field')
            self.assertEquals(token.value, name)

    def assertTokens(self, tokens, formats):
        """Asserts a bunch of tokens at a time."""
        for format, token in zip(formats, tokens):
            self.assertToken(token, *format)

class QueryParserTest(TokenTestCase):

    def test_base_types(self):
        """Test that strings, numbers, and lists behave."""
        t = q.number.parse('1')[0]
        self.assertToken(t, int, 1)
        t = q.number.parse('31230')[0]
        self.assertToken(t, int, 31230)
        t = q.number.parse('5.0')[0]
        self.assertToken(t, float, 5.0)
        t = q.number.parse('.12')[0]
        self.assertToken(t, float, .12)
        t = q.number.parse('1.')[0]
        self.assertToken(t, float, 1.)
        t = q.string.parse('"hello, world"')[0]
        self.assertToken(t, basestring, 'hello, world')
        t = q.string.parse('"hello\\", quote"')[0]
        self.assertToken(t, basestring, 'hello", quote')
        t = q.list_.parse('("1.0", 1.0, 1)')[0]
        self.assertToken(t, list)
        self.assertEquals(len(t), 3)
        self.assertTokens(t, ([basestring,'1.0'], [float,1.0], [int,1]))

        invalid_syntax = {
            'q.list_' : (
                '("foo", 1, 1.4, field)', # no fields in lists
                '("foo", 1 1.4)', # missing comma
                '()', # no empty lists
                '(1,)', #extra comma
            ),
            'q.string' : (
                '"hello', # unterminated
                '"hello"world"', # unescaped quote
            ),
            'q.number' : (
                '1.a', # not a number
                '1.2.3', # invalid float
            )
        }
        for key in invalid_syntax:
            items = invalid_syntax[key]
            for item in items:
                self.assertRaises(ME, eval(key).parse, (item))

    def test_field_list(self):
        """Test that 'field lists' behave (lists of fields, no values)."""
        parse = q.field_list.parse
        tokens = parse('(foo, bar, baz)')
        self.assertEquals(len(tokens), 1)
        tokens = tokens[0]
        self.assertEquals(len(tokens), 3)
        f = 'field'
        self.assertTokens(tokens, ([f,'foo'], [f,'bar'], [f,'baz']))
        tokens = parse('(foo)')
        self.assertEquals(len(tokens), 1)
        tokens = tokens[0]
        self.assertEquals(len(tokens), 1)
        self.assertToken(tokens[0], 'field', 'foo')

        invalid_syntax = (
            '(foo, bar, 1)', # contains an integer
            '(foo, bar, 1.5)', # contains a float
            '(foo  bar, baz)', # missing comma
            '("foo", bar, baz)', # contains a string
            '(,)', # can't have a comma with no field
            '()', # no empty field lists
        )
        for string in invalid_syntax:
            self.assertRaises(ME , parse, (string))

    def test_where_clause(self):
        """Make sure WHERE clauses work.

        Note none of this can test that the logic resultant from these WHERE
        clauses can make any sense, just that they parse as syntactically
        correct."""
        parse = q.where_clause.parse
        string = lambda x: [basestring, x]
        field = lambda x: ['field', x]
        iso = field('iso')
        tokens = parse('iso > 40')
        self.assertEquals(len(tokens), 3)
        self.assertTokens(tokens, (iso, ['gt'], [int,40]))
        tokens = parse('iso < 10 AND iso >= 3 OR iso <= 3')
        self.assertEquals(len(tokens), 11)
        self.assertTokens(tokens, (iso, ['lt'], [int,10], ['and'], iso,
            ['gte'], [int,3], ['or'], iso, ['lte'], [int,3])) 
        tokens = parse('foo in ("italy", "portugal", "spain") AND bar < 300')
        self.assertEquals(len(tokens), 7)
        self.assertTokens(tokens, (field('foo'), ['in'], [list], ['and'], field('bar'), ['lt'], [int,300]))
        self.assertTokens(tokens[2], (string("italy"), string("portugal"), string("spain")))

        invalid_syntax = (
            '"foo" in ("italy", "portugal")', # "foo" not a field
            'foo < "10"', # '<' is not valid string expr operator
            'foo < ("10")', # '<' not valid list expr operator
            '10 > 3', # first must be a field
        )
        for string in invalid_syntax:
            self.assertRaises(ME, parse, (string))

    def test_find_statement(self):
        """Test that find statements work."""
        parse = q.find_stmt.parse
        valid_wheres = (
            'iso < 200',
            'iso > 100 and tag in ("italy", "portugal", "spain")',
            'aperture > 2.3 or shutter < 0.1'
        )
        valid_stmts = (
            'find 10 where %s',
            'find 10 (path, iso) where %s',
            'find (path,iso)',
            'find (path, iso) where %s',
            'find where %s',
            'find',
        )
        where_lengths = (3, 7, 7)
        stmt_lengths = (3, 4, 2, 3, 2, 1)
        def test_tokens(index, tokens):
            if index == 0:
                self.assertTokens(tokens[:3], (['find'], (int,10), ['where']))
            elif index == 1:
                self.assertTokens(tokens[:4], (['find'], (int,10), [list], ['where']))
            elif index == 2:
                self.assertTokens(tokens[:2], (['find'], [list]))
            elif index == 3:
                self.assertTokens(tokens[:3], (['find'], [list], ['where']))
            elif index == 4:
                self.assertTokens(tokens[:2], (['find'], ['where']))
            elif index == 5:
                self.assertTokens(tokens, (['find'],))

        for i,stmt in enumerate(valid_stmts):
            if '%s' in stmt:
                for j,w in enumerate(valid_wheres):
                    tokens = parse(stmt % w)
                    self.assertEquals(len(tokens), where_lengths[j] + stmt_lengths[i])
            else:
                tokens = parse(stmt)
            test_tokens(i, tokens)


class FindStatementTest(TokenTestCase):
    def assertStatement(self, statement, count, field_len, spec):
        self.assertEquals(statement.count, count)
        self.assertEquals(len(statement.fields), field_len)
        self.assertEquals(statement.spec, spec)

    def test_basic_queries(self):
        find = q.FindStatement("find")
        self.assertStatement(find, 0, 0, {})
        find = q.FindStatement("find 10")
        self.assertStatement(find, 10, 0, {})
        find = q.FindStatement("find (iso, path, aperture)")
        self.assertStatement(find, 0, 3, {})
        find = q.FindStatement("find 15 (iso)")
        self.assertStatement(find, 15, 1, {})

    def test_where_queries(self):
        find = q.FindStatement("find 10 (iso, path) where iso <= 400")
        self.assertStatement(find, 10, 2, {'iso' : {'$lte':400}})
        self.assertEquals(find.fields, ['iso', 'path'])
        self.assertEquals(len(find.queries), 1)
        self.assertTokens(find.queries[0], ([str, 'iso'], ['lte'], [int, 400]))
        find = q.FindStatement("find 10 where iso < 200")
        self.assertStatement(find, 10, 0, {'iso' : {'$lt':200}})
        find = q.FindStatement("find where shutter > 0.5")
        self.assertStatement(find, 0, 0, {'shutter':{'$gt':0.5}})
        find = q.FindStatement('find where caption = "hello world"')
        self.assertStatement(find, 0, 0, {'caption' : 'hello world'})
        find = q.FindStatement('find where tags in ("italy", "portugal")')
        self.assertStatement(find, 0, 0, {'tags' : {'$in':['italy', 'portugal']}})

    def test_and_queries(self):
        find = q.FindStatement('find 5 where iso < 200 and tags in ("italy", "portugal")')
        self.assertStatement(find, 5, 0, {'iso':{'$lt':200}, 'tags':{'$in':['italy','portugal']}})
        find = q.FindStatement("find where iso < 200 and iso >= 100")
        self.assertStatement(find, 0, 0, {'iso':{'$lt':200,'$gte':100}})

    def test_or_queries(self):
        find = q.FindStatement('find 10 (iso) where iso > 200 or tags in ("italy")')
        self.assertStatement(find, 10, 1, {'$or' : [{'iso':{'$gt':200}}, {'tags': {'$in':['italy']}}]})


