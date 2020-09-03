.. Gencove's CLI documentation master file, created by
   sphinx-quickstart on Sun Aug  4 13:40:16 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gencove's CLI documentation!
===============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. automodule:: gencove.cli
   :members:

Supported Python versions are 3.7 and above.

Quickstart
==========

.. _installation-guide:

Installation
------------

To check your default Python version, open an interactive shell and run:

.. code::

   python --version

To check if you have Python 3, open an interactive shell and run:

.. code::

   python3 --version

To install |cli|, open an interactive shell and run:

.. code::

   python<version> -m pip install gencove

If you want |cli| to be installed for your default Python installation,
you can instead use:

.. code::

   python -m pip install gencove

Using Gencove CLI Tool
----------------------

To start using |cli|, open an interactive shell and run:

.. code::

   gencove --help

This will output all available commands.

.. click:: gencove.cli:cli
   :prog: gencove
   :show-nested:
   :commands: upload,download,projects,uploads

