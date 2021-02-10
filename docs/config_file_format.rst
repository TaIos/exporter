Config file format
===================

Config file is required and is passed by ``-c, --config`` option.
It must contain GitHub and GitLab tokens.
Application uses them for accessing GitHub and GitLab API.


Example
-------

Below is the only valid format of a config file.

.. code-block:: none

    [gitlab]
    token=XXXXXXXXXXXXXXXXXXXX

    [github]
    token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
