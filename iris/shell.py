#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A command shell specifically for iris with a special purpose SQL-like
query language.

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


lstring = String()   > token('string')
lnum  = Float()      > token('number')
lws   = Whitespace() > token('whitespace')
lLiteral = lambda x: Literal(x) > token('literal')

class Lexers(object):
    """These semantically void matchers will match any valid (and many
    invalid) forms for their respective types.  They're used by the
    Completers to figure out what to do."""
    with DroppedSpace():
        FieldList = lLiteral("(") & ( field | comma | lws | lLiteral(")"))[:]
        WhereClause = field & (operator | lstring | lnum | list_ | AND | OR | lws | unknown)[:]

for key in Lexers.__class__.__dict__:
    try: getattr(Lexers, key).config.no_full_first_match()
    except: pass

def dbg(func):
    def wrapped(*args):
        print '<<%s: %s>>' % (func.__name__, '::'.join(args))
        return func(*args)
    return wrapped

def print_exceptions(func):
    def wrapped(*args):
        try: return func(*args)
        except:
            import traceback
            print ''
            traceback.print_exc()
    return wrapped

class FieldListCompleter(object):
    """Tab completer for field lists.  Note that the 'line' here should
    start earliest at '(', and in general it will ignore "text" and use
    its own lexer instead."""
    default = ['iso', 'tags', 'shutter', 'resolution', 'x', 'y', 'fstop', 'aperture']
    def __init__(self, line):
        self.line = line
        try: self.tokens = Lexers.FieldList.parse(line)
        except: self.tokens = None

    def complete(self):
        if not self.tokens: return []
        text_tokens = [t for t in self.tokens if str(t).strip()]
        final = text_tokens[-1]
        final_ws = self.tokens[-1].is_ws()
        if final == '(':
            return self.default
        if final == ',':
            if final_ws:
                return self.default
            return [' ']
        if final.is_field():
            #print '\n%r (%s)' % (self.tokens, 'ws' if final_ws else 'not ws')
            if str(final) in self.default and not final_ws:
                return [str(final)+', ']
            elif str(final) in self.default and final_ws:
                return [')']
            return [f for f in self.default if f.startswith(str(final))]
        return self.default

class WhereCompleter(object):
    def __init__(self, line):
        self.line = line

    def complete(self):
        if not self.line: return ['where']
        return [x for x in ['where', 'WHERE'] if x.startswith(self.line)]

class FindCompleter(object):
    """Tab completer for the 'find' command."""
    def __init__(self, text, line):
        self.text = text
        self.line = line
        self.toks, self.state = statement.match(line).next()
        self.remainder = self.state.text

    def complete(self):
        default = ['<count>', '<field list>', 'WHERE']
        if len(self.toks) == 1:
            if not self.remainder.strip():
                return default
            return FieldListCompleter(self.remainder).complete() or\
                    WhereCompleter(self.remainder).complete()
        if len(self.toks) == 2:
            if isinstance(self.toks[1], int):
                if not self.remainder and self.line[-1].isdigit():
                    return [str(self.toks[1])+' ']
                elif not self.remainder:
                    return [d for d in default if d != '<count>']
                return FieldListCompleter(self.remainder).complete() or\
                        WhereCompleter(self.remainder).complete()
            else: # it's a field list i guess
                return WhereCompleter(self.remainder).complete()
        if len(self.toks) == 3:
            return WhereCompleter(self.remainder).complete()


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

    def _do_statement(self, params, stmt, name):
        try:
            tokens = stmt.parse(name + ' ' + params)
            print tokens
        except Exception, e:
            self._handle_stream_exception(e)

    def do_find(self, params):
        self._do_statement(params, find_stmt, 'find')

    @print_exceptions
    def complete_find(self, text, line, *args):
        return FindCompleter(text, line).complete()

    def do_count(self, params):
        self._do_statement(params, count_stmt, 'count')

    def do_tag(self, params):
        self._do_statement(params, tag_stmt, 'tag')

def prompt():
    parser = CommandParser()
    intro = "iris shell version: %s\n%s" % (bold(version, white), parser._general_help(True))
    parser.cmdloop(intro)

def query(q):
    return CommandParser().onecmd(q)

if __name__ == '__main__':
    try: prompt()
    except KeyboardInterrupt: print

