#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Backend data helpers for iris.

Iris uses mongodb because it's web scale."""

import pymongo

def get_database(host=None, port=None):
    """Get the iris mongo db from host and port.  If none are supplied, attempt
    to read an iris configuration file.  If it doesn't exist, connect to
    localhost:27017."""
    if host is None or port is None:
        from iris import config
        cfg = config.IrisConfig()
        try:
            cfg.read()
            host, port = cfg.host, cfg.port
        except:
            host, port = 'localhost', 27017
    connection = pymongo.Connection(host, port)
    return connection.iris
