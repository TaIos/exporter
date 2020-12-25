#################################################
Quicstart
#################################################

**************
How to install
**************

Install from `PyPi <https://pypi.org/project/fit-ctu-gitlab-exporter/>`_

.. code-block:: bash

	$ pip install fit-ctu-gitlab-exporter


********
Examples
********

==============================================
Export selected projects from GitLab to GitHub
==============================================

.. code-block:: Bash

	$ exporter -c config -p projects


where content of file ``config`` looks like this

::

 [gitlab]
 token=XXXXXXXXXXXXXXXXXXXX

 [github]
 token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

and content of file ``projects`` looks like this

::

	my_cpp_project
	java_test
	progtest_pray_god
