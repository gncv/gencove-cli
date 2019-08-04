.. Gencove's CLI documentation master file, created by
   sphinx-quickstart on Sun Aug  4 13:40:16 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gencove's CLI documentation!
===============================================

.. automodule:: gencove.cli
   :members:

Supported Python versions are 2.7+ and 3.7+.

Quickstart
==========

.. _installation-guide:

Installation
------------

To check your default Python version, open an interactive shell and run:

.. code-block::

   python --version

To check if you have Python 3, open an interactive shell and run:

.. code-block::

   python3 --version

To install |cli|, open an interactive shell and run:

.. code-block::

   python<version> -m pip install gencove

If you want |cli| to be installed for your default Python installation,
you can instead use:

.. code-block::

   python -m pip install gencove

Using Gencove CLI Tool
----------------------

To start using |cli|, open an interactive shell and run:

.. code-block::

   gencove --help

This will output all available commands.

.. click:: gencove.cli:cli
   :prog: gencove
   :show-nested:
   :commands: sync


.. toctree::
   :maxdepth: 2
   :caption: Contents:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
