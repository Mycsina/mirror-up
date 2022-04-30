=========
mirror-up
=========

.. image:: https://readthedocs.org/projects/mirror-up/badge/?version=latest
        :target: https://mirror-up.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Upload your files to MirrorAce


Quickstart
--------------

Install the package from PyPi

.. code-block:: console

        $ pip install mirror-up

Create an account at MirrorAce and set your environment variables

.. code-block:: console

        MirAce_K=     # MirrorAce API key
        MirAce_T=   # MirrorAce API Token
        ZIP_SAVE=    # Path where to store temp files

Upload the file/folder at a given path to MirrorAce

.. code-block:: console

        $ python -m mirror_up mirror_ace upload PATH...

Upload all files inside given folder as separate uploads

.. code-block:: console

        $ python -m mirror_up mirror_ace folder PATH...

* Free software: MIT
* Documentation: https://mirror-up.readthedocs.io.


Credits
-------

This package was created with Cookiecutter_ and the `briggySmalls/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`briggySmalls/cookiecutter-pypackage`: https://github.com/briggySmalls/cookiecutter-pypackage
