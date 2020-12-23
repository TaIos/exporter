from helper import run

hlp_m = run('--help')
hlp_e = run('--help', entrypoint=True)
stdout_m = hlp_m.stdout
stdout_e = hlp_e.stdout


def test_description():
    description = 'Tool for exporting projects from FIT CTU GitLab to GitHub'
    assert description in stdout_m
    print('<<<<<<<<<<<<<')
    print(hlp_e.stderr)
    print('<<<<<<<<<<<<<')
    assert description in stdout_e
