#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parsers meant for completion.  Note that the term 'lexer' is a little off
here;  these are just extremely lenient parsers that are probably horribly
slow lexers.  Eventually it may make sense to create our own tokenizer or
to use the LEPL lexing facilities directly."""

import re
from lepl import *

class LexerToken(object):
    """Embeds most types of tokens for our parser."""
    keywords = ('find', 'count', 'tag', 'where', 'and', 'or', 'in')
    def __init__(self, type, value):
        self.type = type.lower()
        self.value = value[0] if isinstance(value, list) else value

    def is_field(self): return self.type == 'field'
    def is_ws(self): return self.type == 'whitespace'
    def is_unk(self): return self.type == 'unknown'
    def __repr__(self): return '<%s: %s>' % (self.type, self.value)
    def __eq__(self, other):
        return self.value == other
    def __str__(self): return str(self.value)

def Insensitive(string):
    """A case insensitive literal."""
    return Regexp(re.compile(string, re.I))

def token(name):
    """Generates a function that returns a curried token."""
    return lambda value: LexerToken(name, value)

where           = Literal('where')                  > token('where')
lparen          = Literal("(")                      > token('sep')
rparen          = Literal(")")                      > token('sep')
comma           = Literal(",")                      > token('sep')
operator        = Insensitive('={1,2}|<=|<|>=|>|in')     > token('operator')
andor           = Insensitive('(and)|(or)')         > token('operator')

field           = Regexp('[a-zA-Z][-a-zA-Z0-9_]*')  > token('field')
unknown         = Regexp('.+')                      > token('unknown')
string          = String()                          > token('string')
num             = Float()                           > token('number')
ws              = Whitespace()                      > token('whitespace')

# The lexers are basically (first token) & ( any | other | valid | tokens )
# We need to catch whitespace because the tab on the end of the final token
# vs the tab a space after the end of the final token actually is different;
with DroppedSpace():
    list_           = lparen & ( string | comma | ws | rparen | num )[:]
    field_list      = lparen & ( field | comma | ws | rparen )[:]
    where_clause    = field & (operator | string | num | list_ | ws | unknown)[:]

field_list.config.no_full_first_match()
where_clause.config.no_full_first_match()

