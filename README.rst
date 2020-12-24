.. contents::

#################################################
Exporter: FIT CTU GitLab to GitHub project export
#################################################

****
Goal
****

Sometimes I need to export projects from FIT CTU `GitLab <https://gitlab.fit.cvut.cz/>`_ to GitHub. It can be done `manually <https://stackoverflow.com/a/22266000/6784881>`_, but for a larger amount of projects, it is very time-consuming. For example, if you finish your studies at FIT CTU, you immediately lose access to your GitLab and all of your projects (even if you continue your studies, in a meantime you lose access).

************
Known issues
************

#. Synchronization of big files. FIT CTU GitLab allows files bigger than 200MB to be stored. GitHub does not. Git LFS can be used instead.
#. Access control works differently in GitLab and GitHub


************************
Requirements for grading
************************

#. Use ``requests`` (or some asyncio alternative, such as ``aiohttp`` or ``httpx``) for communicating with GitLab and GitHub API

#. Use some Python git wrapper or git directly to manipulate with cloned repositories (eg setting different upstream)

#. Create a command line interface, which will at least allow

   #. Specify a list of repository names for exporting

   #. Set policy for conflicts, eg project with the same name already exists on GitHub => overwrite

#. Inform user about the exporting process by terminal output and also store this information in logs

#. Load configuration from a file using ``configparser`` (or similar), at least allowing to use own API keys

#. Write tests using ``pytest``, also allow to run them using ``tox``

   #. Fake both API for testing
   #. Test internal functionality

#. Make it available on PyPI as a package under a free software license

#. Document project using docstrings in code and this README, generate Sphinx documentation via a tox environment

#############
Documentation
#############
