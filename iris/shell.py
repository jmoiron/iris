#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A command shell specifically for iris with a special purpose SQL-like
query language.

"""

import readline
import cmd

from iris import version
from iris.utils import color, bold, white, green, red

from iris.query import parser, completion

import logging
logger = logging.getLogger("lepl")
logger.setLevel(logging.CRITICAL)


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
        if ret: return string
        print string

    def do_help(self, params):
        """Get general help or help on specific commands."""
        if not params:
            self._general_help()
        elif params == 'commands':
            print '  '.join(self._commands)
        else:
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
        return completion.FindStatement(text, line).complete()

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

