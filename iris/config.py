#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Configuration for Iris."""

import os
import sys

import ConfigParser
import optparse

class IrisConfig(object):
    """ConfigParser is so upsetting I never want to deal with it personally."""

    def __init__(self, path='~/.iris.cfg'):
        self.path = os.path.expanduser(path)
        try: self.read()
        except: pass

    def read(self):
        """Read the configuration file."""
        if not os.path.exists(self.path):
            raise Exception("Config file `%s` does not exist." % self.path)
        config = ConfigParser.SafeConfigParser()
        config.read(self.path)
        self.config = config

    def generate(self, force=False):
        """Generate a default configuration and write it to self.path.
        If there is a file there already, fail quietly unless force is True."""
        if os.path.exists(self.path):
            return
        config = ConfigParser.SafeConfigParser()
        config.add_section('iris')
        config.add_section('db')
        config.set('db', 'host', '127.0.0.1')
        config.set('db', 'port', '27017')
        with open(self.path, 'w') as config_file:
            config.write(config_file)
        self.config = config

    @property
    def host(self):
        try: return self.config.get('db', 'host')
        except: return None

    @property
    def port(self):
        try: return int(self.config.get('db', 'port'))
        except: return None

