Return codes
============

After export is finished, user is presented with the result.

Result for each export may contain multiple codes:

#. ``EXPORTED``

   Project has been successfully exported.

#. ``SKIPPED``

   Export for this project has been skipped because it's name already exists in GitHub (only without ``overwrite`` flag).

#. ``SUCCESS_ROLLBACK``

   Everything for the project export is undone. Eg deleting created GitHub repo if it did not exist before.

#. ``ERROR_ROLLBACK``

   Error during rollback.

#. ``RUN_ERROR``

   Error during run of the export. Does not interfere with ``SUCCESS_ROLLBACK``.

#. ``NOT_RUNNED``

   Export has not been started for this project.

#. ``OVERWRITTEN``

   GitHub project has been overwritten (only with ``overwrite`` flag).

#. ``INTERRUPTED``

   Run of the export has been interrupted by the user (by sending ``Ctrl+C``). Does not interfere with ``SUCCESS_ROLLBACK``.

#. ``DRY_RUN``

   Application was run in ``dry-run`` mode. No changes were made.

#. ``NO_GITLAB_PROJECT``

   There is not GitLab project for the given name.

#. ``MULTIPLE_GITLAB_PROJECTS``

   There are multiple GitLab projects for the given name.
