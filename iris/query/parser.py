#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parser for iris shell queries.  To see a BNF-style description of the
query language, check ``iris/query/language.bnf``."""

import re
from lepl import *

# make lepl's logging behave
import logging
logger = logging.getLogger("lepl")
logger.setLevel(logging.CRITICAL)

class IrisToken(object):
    """Embeds most types of tokens for our parser."""
    keywords = ('find', 'count', 'tag', 'where', 'and', 'or', 'in')
    def __init__(self, type, value):
        self.type = type.lower()
        self.value = value[0] if isinstance(value, list) else value

    def is_field(self): return self.type == 'field'
    def is_ws(self): return self.type == 'whitespace'
    def is_unk(self): return self.type == 'unknown'
    def __repr__(self):
        if self.type in self.keywords:
            return '<%s>' % self.type
        if self.type == 'field':
            return '<:%s>' % self.value
        return '<%s (%r)>' % (self.type, self.value)
    def __eq__(self, other):
        return self.value == other
    def __str__(self): return str(self.value)

def token(name):
    """Generates a function that returns a curried token."""
    return lambda value: IrisToken(name, value)

def Insensitive(string):
    """A case insensitive literal."""
    return Regexp(re.compile(string, re.I))

def Separator(matcher, drop=True, ws=~Whitespace()[:]):
    """Create space-tolerant separators for repetitions."""
    if drop: return ws & Drop(matcher) & ws
    return ws & matcher & ws

def CommaSeparated(matcher, min=1, comma=Literal(',')):
    """Use the matcher as a comma separated value within ()'s."""
    return Drop("(") & matcher[min:, Separator(comma)] & Drop(")")

def numerify(x):
    """Cast a string to a number of appropriate type."""
    value = x[0]
    try: return int(value)
    except ValueError: return float(value)


# types
Alpha = Regexp('[a-zA-Z]+')
AlphaNum = Regexp('[a-zA-Z0-9]+')
InitialAlpha = Regexp('[a-zA-Z][-a-zA-Z0-9_]*')

# tokens
find    = Insensitive("find")               > token('find')
count   = Insensitive("count")              > token('count')
tag     = Insensitive("tag")                > token('tag')
where   = Insensitive("where")              > token('where')
AND     = Insensitive("and") | Literal("&") > token('and')
OR      = Insensitive("or")  | Literal("|") > token('or')
field   = InitialAlpha                      > token('field')

# special tokens
unknown = Regexp('.+')                      > token('unknown')

# data types
string  = String()
number  = Float()                           > numerify
list_   = CommaSeparated(string | number)   > list

# operators
in_oper     = Insensitive("in")     > token('in')
equal       = Literal("=")          > token('equal')
dblequal    = Literal("==")         > token('dblequal')
lt          = Literal("<")          > token('lt')
lte         = Literal("<=")         > token('lte')
gt          = Literal(">")          > token('gt')
gte         = Literal(">=")         > token('gte')

number_operator = dblequal | equal | lte | gte | lt | gt
string_operator = in_oper | equal | dblequal
list_operator   = in_oper
operator        = in_oper | number_operator

# expressions
with DroppedSpace():
    field_list  = CommaSeparated(field) > list
    num_expr    = number_operator & number
    string_expr = string_operator & string
    list_expr   = list_operator & list_
    logic_expr  = field & (num_expr | string_expr | list_expr)
    where_clause = logic_expr[1:, Separator(AND | OR, drop=False)]
    where_expr  = where & where_clause
    where_expr.config.auto_memoize()


# statements
with DroppedSpace():
    find_stmt   = find & number[:1] & field_list[:1] & where_expr[:]
    count_stmt  = count & where_expr[:]
    tag_stmt    = tag & (string | list_) & where_expr

statement = find_stmt | count_stmt | tag_stmt
statement.config.no_full_first_match()
statement.config.auto_memoize()

def parse_statement(string):
    return statement.parse(string)
