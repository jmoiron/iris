iris
----

Iris is a photo management application with the aim of collecting metadata
about your photos.  It aims to be a tool that both excels at batch operations
and liberates your photo metadata to make querying things easier.  It is
meant to work side-by-side with traditional desktop photo managers like F-Spot
or Picasa, but the goal is to be able to answer questions that these types
of managers find difficult, like "How many photos of my girlfriend did I
take in Paris?", or "Sync > 4.5 star photos tagged 'italy' to my flickr."

requirements
============

Unfortunately, *iris* requires software that is not straightforward to install:

* pyexiv2_ >= 2.2.0
* mongodb_ = 1.6.3

.. _pyexiv2: http://tilloy.net/dev/pyexiv2/
.. _mongodb: http://www.mongodb.org/

*iris* might work on older versions of *mongodb* (and with older versions of
the client library *pymongo*), but was developed using the versions listed.
*iris* also requires these python modules, installable via *pip* and usually 
pulled in automatically during a *pip* install of iris:

* cmdparse_
* pymongo_ >= 1.9

.. _cmdparse: http://github.com/jmoiron/python-cmdparse
.. _pymongo: http://api.mongodb.org/python/1.9%2B/index.html

usage
=====

Everything below is lies::

  iris tag *.jpg

