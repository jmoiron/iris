#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Completion helpers for iris queries.  These use partial/lexing query
parsers to determine what tokens should come next.  Because of limitations
either in LEPL or my knowledge of LEPL, I'm not able to use the real parsers
directly to determine what tokens types could come next to satisfy the
language syntax, so extra code must be written to do so.


See also, some interesting notes on implementing various types of simple
command grammars using gnu/readline & python:

    https://www.ironalbatross.net/wiki/index.php5?title=Python_Readline_Completions
    https://www.ironalbatross.net/wiki/index.php5?title=Python_Cmd_Completions
"""

from iris.query import lexer
from iris.query import parser

class FindStatement(object):
    """Tab completer for the 'find' command."""
    def __init__(self, text, line):
        self.text = text
        self.line = line
        self.toks, self.state = parser.statement.match(line).next()
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

class FieldListCompleter(object):
    """Tab completer for field lists.  Note that the 'line' here should
    start earliest at '(', and in general it will ignore "text" and use
    its own lexer instead."""
    default = ['iso', 'tags', 'shutter', 'resolution', 'x', 'y', 'fstop', 'aperture']
    def __init__(self, line):
        self.line = line
        try: self.tokens = lexer.field_list.parse(line)
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
