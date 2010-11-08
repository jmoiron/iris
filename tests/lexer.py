#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""iris query tests."""

from unittest import TestCase
from iris.query import lexer as l

ME = l.FullFirstMatchException

class LexerTokenTest(TestCase):
    def assertToken(self, token, type, name=None):
        if isinstance(token, list) and len(token) == 1:
            token = token[0]
        """Assert one token is of a type and, possibly, a value."""
        if type in(int, float, str, list):
            self.assertTrue(isinstance(token, type))
            if name:
                self.assertEquals(token, name)
        else:
            self.assertEquals(token.type, type)
            self.assertEquals(token.value, name)

    def test_miscellaneous(self):
        self.assertToken(l.lparen.parse('('), 'sep', '(')
        self.assertToken(l.rparen.parse(')'), 'sep', ')')
        self.assertToken(l.comma.parse(','), 'sep', ',')
        self.assertRaises(ME, l.lparen.parse, (')'))
        self.assertRaises(ME, l.rparen.parse, ('('))
        self.assertRaises(ME, l.comma.parse, ('3'))

    def test_operators(self):
        parse = l.operator.parse
        self.assertToken(parse('='), 'operator', '=')
        self.assertToken(parse('=='), 'operator', '==')
        self.assertToken(parse('<='), 'operator', '<=')
        self.assertToken(parse('>='), 'operator', '>=')
        self.assertToken(parse('<'), 'operator', '<')
        self.assertToken(parse('>'), 'operator', '>')
        self.assertToken(parse('in'), 'operator', 'in')

