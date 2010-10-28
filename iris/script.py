#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Support for the iris script."""

from cmdparse import Command, CommandParser

class AddCommand(Command):
    """Add a photo or directory of photos."""
    def __init__(self):
        Command.__init__(self, "add", summary="add files or directories.")
        self.add_option('-r', '--recursive', action='store_true', default=False)

    def run(self, options, args):
        print "add: ", options, args

class TagCommand(Command):
    """Tag one or more photos.

    You can tag photos based on filename:
        iris tag photos/italy/*.JPG

    Or via a query on iris' database:
        iris tag -q ...
    """
    def __init__(self):
        Command.__init__(self, "tag", summary="tag photos by filename, query, etc.")
        self.add_option('-r', '--recursive', action='store_true', default=False)

    def run(self, options, args):
        print "tag: ", options, args

class HelpCommand(Command):
    """Provides extended help for other commands."""
    def __init__(self):
        Command.__init__(self, "help", summary="extended help for other commands.")
    
    def run(self, options, args):
        if not args:
            self.parser.print_help()
            return
        name = args[0]
        cmd = self.parser.find_command(name)
        print cmd.__doc__
        cmd.print_help()

def main():
    parser = CommandParser()
    parser.add_command(HelpCommand())
    parser.add_command(AddCommand())
    parser.add_command(TagCommand())
    command, options, args = parser.parse_args()
    if command is None:
        parser.print_help()
        return 0
    try:
        return command.run(options, args)
    except KeyboardInterrupt:
        return -1

