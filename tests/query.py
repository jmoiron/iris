#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""iris query tests."""

from unittest import TestCase
from iris import query as q

ME = q.FullFirstMatchException

class QueryParserTest(TestCase):

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
        """Make sure WHERE clauses work.  Note none of this can test that
        the logic resultant from these WHERE clauses can make any sense,
        just that they parse as syntactically correct."""
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

