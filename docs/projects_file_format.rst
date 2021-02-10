Projects file format
====================

Projects file is required and is passed by ``--projects, -p`` option.
Each line corresponds to one exported project. Format of each line is ::

    gitlab_name [-> github_name] [private/public]


Example
#######

Below is an example of a valid project file. Every format is used here.

.. code-block:: none
   :linenos:

   my_project
   my_secret_project private
   ag1_progtest -> avl_tree_cpp
   fit_bachelor_thesis -> bachelor_thesis public
   fit_bachelor_thesis -> bachelor_thesis_backup private

Explanation of each line

#. Specify only the GitLab project name. GitHub name is the same and visibility is default. ::

    my_project

#. Same as above but explicitly set visibility of exported GitHub project. ::

    my_secret_project private

#. Set different GitHub name to export to. ::

    ag1_progtest -> avl_tree_cpp

4-5. Explicitly add visibility with a different name on GitHub. ::

    fit_bachelor_thesis -> bachelor_thesis public
    fit_bachelor_thesis -> bachelor_thesis_backup private

