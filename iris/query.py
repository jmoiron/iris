#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""My own special query language for iris, because I'm an idiot.

See also, some interesting notes on implementing various types of simple
command grammars using gnu/readline & python:
    https://www.ironalbatross.net/wiki/index.php5?title=Python_Readline_Completions
    https://www.ironalbatross.net/wiki/index.php5?title=Python_Cmd_Completions

Something even more complex might eventually be needed.

If you can't read the LEPL code below, this is a rough BNF translation:

<alpha> ::= { a..z | A..Z }
<num> ::= { 0..9 }
<alphanum> ::= { alpha | num }
<initialalpha> ::= alpha { alphanum }

# tokens
find ::= find
count ::= count
where ::= where
tag   ::= tag
and   ::= (AND | &)
or    ::= (OR | "|")
field ::= <initialalpha>
EOL ::= "\n"

# data
string ::= '"' { <alphanum> } '"'
number ::= { <num> } [ "." { <num> }]
list   ::= "(" ( string | number ) { "," ( string | number ) } ")"
literal ::= ( string | number | list )

# comparisons
equal ::= "="           # implied '*foo*' for strings
doubleequal ::= "=="    # precisely equal
lt ::= "<"
gt ::= ">"
lte ::= lt equal
gte ::= gt equal
comps ::= ( equal | doubleequal | lt | gt | gte | lte )

in  ::= "in"

# expressions
field_list ::= "(" field { "," field} ")"
comparison ::= field comps literal
in_expr ::= field in list
where_clause ::= where ( comparison | in_expr ) [ { (and | or) (comparison | in_expr ) } ]

# statements
find_stmt ::= find [number] [field_list] [where_clause] EOL
count_stmt ::= count [where_clause] EOL
tag_stmt ::= tag string where_clause EOL

"""

import readline
import cmd
import sys
import re

from iris import version
from iris.utils import color, bold, white, green, red

from lepl import *

import logging
logger = logging.getLogger("lepl")
logger.setLevel(logging.CRITICAL)

class Token(object):
    tokens = ('find', 'count', 'tag', 'where', 'and', 'or', 'in')
    def __init__(self, type, value):
        self.type = type.lower()
        self.value = value[0] if isinstance(value, list) else value

    def __repr__(self):
        if self.type in self.tokens:
            return '<%s>' % self.type
        if self.type == 'field':
            return '<:%s>' % self.value
        return '<%s (%r)>' % (self.type, self.value)
    def __str__(self): return str(self.value)

def token(name):
    """Generates a function that returns a curried token."""
    return lambda value: Token(name, value)

def Insensitive(string):
    """A case insensitive literal."""
    return Regexp(re.compile(string, re.I))

ws = ~Whitespace()[:]

def Separator(matcher, drop=True):
    if drop:
        return ws & Drop(matcher) & ws
    return ws & matcher & ws

def numerify(x):
    value = x[0]
    try:
        return int(value)
    except ValueError:
        return float(value)

# types
Alpha = Regexp('[a-zA-Z]+')
AlphaNum = Regexp('[a-zA-Z0-9]+')
InitialAlpha = Regexp('[a-zA-Z][-a-zA-Z0-9_]*')

# tokens
find    = Insensitive("find")               > token('find')
count   = Insensitive("count")              > token('count')
tag     = Insensitive("tag")                > token('tag')
where   = Insensitive("where")              > token('where')
AND     = Insensitive("and") | Literal("&")     > token('and')
OR      = Insensitive("or")  | Literal("|")     > token('or')
field   = InitialAlpha    > token('field')
comma   = Literal(",")
eol     = Eos()

def CommaSeparated(matcher, min=1):
    return Drop("(") & matcher[min:, Separator(comma)] & Drop(")")

# data types
string  = String()
number  = Float()           > numerify
with DroppedSpace():
    list_   = CommaSeparated(string | number) > list

# operators
in_oper = Insensitive("in")     > token('in')
equal   = Literal("=")          > token('equal')
dblequal = Literal("==")        > token('dblequal')
lt      = Literal("<")          > token('lt')
lte     = Literal("<=")         > token('lte')
gt      = Literal(">")          > token('gt')
gte     = Literal(">=")         > token('gte')

number_operator = dblequal | equal | lte | gte | lt | gt
string_operator = in_oper | equal | dblequal
list_operator   = in_oper

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

# partials
class Partials(object):
    field_list = Literal("(") & field[1:, ws & Drop(",") & ws] & Literal(")")

for key in Partials.__class__.__dict__:
    try: getattr(Partials, key).config.no_full_first_match()
    except: pass

class CommandParser(cmd.Cmd):
    def __init__(self, *args, **kwargs):
        # stupid non-newstyle classes in stdlib
        cmd.Cmd.__init__(self, *args, **kwargs)
        self.prompt = color('iris', green) + ' $ '
        self._commands = [c[3:] for c in dir(self) if c.startswith('do_')]

    def default(self, params):
        if params == 'EOF':
            print
            return 1
        cmd.Cmd.default(self, params)

    def _general_help(self, ret=False):
        string = """Press <TAB> twice or do "%s" to see list of commands.""" % bold('help commands', white)
        if ret:
            return string
        print string

    def do_help(self, params):
        """Get general help or help on specific commands."""
        if not params:
            self._general_help()
            return
        if params == 'commands':
            print '  '.join(self._commands)
            return
        cmd.Cmd.do_help(self, params)

    def complete_help(self, text, line, *args):
        if len(line.split()) > 2:
            return []
        return [x+' ' for x in self._commands if x.startswith(text)]

    def do_debug(self, params):
        """Enter the debugger."""
        import ipdb; ipdb.set_trace();

    def _handle_stream_exception(self, e):
        s = ": invalid syntax (chr %d): " % e.stream.character_offset
        slen = len(s) + 5
        s = bold("Error", red) + s
        print s + bold(e.stream.location[3], white)
        print ' '*slen + ' '*e.stream.character_offset + bold("^", red)

    def do_find(self, params):
        try:
            tokens = find_stmt.parse('find ' + params)
            print tokens
        except Exception, e:
            self._handle_stream_exception(e)

    def _complete_field_list(self, text, line, unparsed):
        """Handle completion of field lists.  Note that there are a finite
        number of fields."""
        fields = ('iso', 'tags', 'shutter', 'resolution', 'x', 'y', 'fstop', 'aperture')
        if text in fields:
            # if text is already completed from the fields, return the comma
            return [', ']
        return [f for f in fields if f.startswith(text)]

    def complete_find(self, text, line, begidx, endidx):
        if line.lower().strip() == 'find' and not text:
            return ['<count>', '<field list>', 'WHERE']
        toks = statement.parse(line)
        if len(toks) == 1:
            # if len is 1, we can have a number, field list, or "where" token;
            field_list

        print toks
        #print '[[', text, line, begidx, endidx, ']]'

    def do_count(self, params):
        try:
            tokens = count_stmt.parse('count ' + params)
            print tokens
        except Exception, e:
            self._handle_stream_exception(e)

    def do_tag(self, params):
        try:
            tokens = count_stmt.parse('tag ' + params)
            print tokens
        except Exception, e:
            self._handle_stream_exception(e)

        print params

def prompt():
    parser = CommandParser()
    intro = "iris shell version: %s\n%s" % (bold(version, white), parser._general_help(True))
    parser.cmdloop(intro)

def query(q):
    return CommandParser().onecmd(q)

if __name__ == '__main__':
    prompt()

