Manpage
==========

.. code-block:: none

    Usage: exporter [OPTIONS]

        Tool for exporting projects from FIT CTU GitLab to GitHub

    Options:
      --version                       Show the version and exit.
      -c, --config FILENAME           File containing GitHub and GitLab tokens.
                                      [required]

      --export-all                    Export all GitLab projects associated with
                                      given token.

      -p, --projects FILENAME         Project names to export. See Documentation
                                      for format. Option is mutually exclusive
                                      with export-all.

      --purge-gh                      Prompt for GitHub token with admin access,
                                      delete all repos and exit. Dangerous!

      --debug                         Run application in debug mode. Application
                                      is unstable in this mode.

      --conflict-policy [skip|overwrite]
                                      [skip] skip export for project names which
                                      already exists on GitHib.[overwrite]
                                      overwrite any GitHub project which already
                                      exists.

      --tmp-dir PATH                  Temporary directory to store data during
                                      export.  [default: tmp]

      --task-timeout FLOAT            Timeout for unresponding export task.
                                      [default: 30.0]

      --unique                        Prevent GitHub name conflicts by appending
                                      random string at the end of exported project
                                      name.

      --visibility [public|private]   Visibility of the exported project on GitHub
                                      [default: private]

      --batch-size INTEGER            Maximum count of simultaneously running
                                      tasks.  [default: 10]

      --dry-run                       Do not perform any changes on GitLab and
                                      Github.

      --help                          Show this message and exit.


