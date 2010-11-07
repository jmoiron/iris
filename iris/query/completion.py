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


