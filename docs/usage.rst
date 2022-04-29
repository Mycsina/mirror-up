=====
Usage
=====

To use mirror-up, run on the console:

.. code-block:: console

    $ python -m mirror_up

-------------
MirrorAce
-------------

Currently, only MirrorAce is supported, so 

.. code-block:: console

    python -m mirror_up mirror_ace

will let you acess the implemented operations.

^^^^^^^^^^^^^^^^
Upload vs folder
^^^^^^^^^^^^^^^^

mirror_ace implements two upload operations: folder and upload.
 
Upload will upload the file/folder found at the given path(s)

.. code-block:: console

    $ python -m mirror_up mirror_ace upload PATH...


Folder will upload the files/folders inside the given folder as separate uploads.

.. code-block:: console

    $ python -m mirror_up mirror_ace folder PATH...

