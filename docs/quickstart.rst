Quickstart
==========

How to install
--------------

Install from `PyPi <https://pypi.org/project/fit-ctu-gitlab-exporter/>`_

.. code-block:: bash

	$ pip install fit-ctu-gitlab-exporter


Examples
--------

| Allowed ``config`` file format is described :doc:`here </config_file_format>`,
| ``projects`` file format is described :doc:`here </projects_file_format>`.

1. Export multiple projects
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: Bash

	$ exporter -c config -p projects

where content of file ``projects`` is

.. code-block:: none

    my_gitlab_project
    my_other_gitlab_project

2. Export, rename and set visibility for multiple projects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: Bash

	$ exporter -c config -p projects

where content of file ``projects`` is

.. code-block:: none

    my_gitlab_project -> avl_tree_cpp
    my_secret_project -> secret_project private


3. Export all projects
^^^^^^^^^^^^^^^^^^^

Export all of your GitLab projects. Run at most ``batch-size`` exports simultaneously.

.. code-block:: Bash

    $ exporter -c config --export-all --batch-size=5


