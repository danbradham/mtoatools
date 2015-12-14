============
Installation
============

Get mtoatools
=============
You can get mtoatools from pypi or directly from git.

PyPi
----
::

    $ pip install mtoatools

Git
---
::

    $ git clone https://github.com//mtoatools.git
    $ cd mtoatools
    $ python setup.py install


Installing the maya shelf
=========================
In maya run the following command from a python tab in your script editor.

::

    import mtoatools.shelf

The mtoatools shelf tab should appear. To reload the mtoatools shelf use python's module reload mechanism.

::

    reload(mtoatools.shelf)

Now you're ready to use mtoatools!
