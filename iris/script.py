#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Support for the iris script."""

import os

from cmdparse import Command, CommandParser
from iris import backend

class AddCommand(Command):
    """Add a photo or directory of photos."""
    def __init__(self):
        Command.__init__(self, "add", summary="add files or directories.")
        self.add_option('-r', '--recursive', action='store_true', default=False)

    def run(self, options, args):
        """Args here are a bunch of file or directory names.  We want to
        mostly defer to other functions that do the stuff for us."""
        for arg in args:
            # TODO: handle error conditions here
            photo = backend.Photo(arg)
            photo._save()

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
        self.add_option('-q', '--query', action='store_true', default=False, help="query instead of paths")

    def run(self, options, args):
        print "tag: ", options, args

class QueryCommand(Command):
    """Query iris' database for photos."""
    def __init__(self):
        Command.__init__(self, "query", summary="query for photos")

    def run(self, options, args):
        print "query: ", options, args

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

class ListCommand(Command):
    def __init__(self):
        Command.__init__(self, "list", summary="list photos in iris")
        self.add_option('-v', '--verbose', action='count', help='increase verbosity')

    def run(self, options, args):
        from iris import utils
        db = backend.get_database()
        photos = [backend.Photo(p) for p in db.photos.find()]
        if options.verbose > 1:
            import pprint
            pprint.pprint([p.__dict__ for p in photos])
        elif options.verbose == 1:
            for photo in photos:
                print '-- %s ' % utils.bold(photo.path)
                tagstr = '  tags: %s' % ', '.join(photo.tags) if photo.tags else ''
                print '  %dx%d, %s%s' % (photo.x, photo.y, utils.humansize(photo.size), tagstr)
        else:
            for photo in photos:
                print photo.path
        print ''
        print '%d photos' % len(photos)

def main():
    import pymongo
    parser = CommandParser()
    parser.add_command(HelpCommand())
    parser.add_command(AddCommand())
    parser.add_command(TagCommand())
    parser.add_command(ListCommand())
    parser.add_command(QueryCommand())
    command, options, args = parser.parse_args()
    if command is None:
        parser.print_help()
        return 0
    try:
        return command.run(options, args)
    except KeyboardInterrupt:
        return -1
    except pymongo.errors.AutoReconnect:
        from iris import config
        cfg = config.IrisConfig()
        host, port = cfg.host, cfg.port
        host = host if host else 'localhost'
        port = port if port else 27017
        utils.error("could not connect to mongodb (%s:%s); is it running?" % (host, port))

