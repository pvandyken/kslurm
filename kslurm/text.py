from __future__ import absolute_import, annotations

SETTINGS_HEADER = "[sky_blue1]SETTINGS[/]"
COMMAND_HEADER = "[sky_blue1]COMMAND[/]"

KBATCH_MSG = f"""
    [green]Scheduling Batch Command[/]
        {SETTINGS_HEADER}
            [white]{{slurm_args}}[/]
        {COMMAND_HEADER}
            {{command}}
"""

KRUN_CMD_MESSAGE = f""" \
    [green]Running job[/]
        {SETTINGS_HEADER}
            [white]{{args}}[/]
        {COMMAND_HEADER}
            [white]{{command}}[/]
"""

INTERACTIVE_MSG = f"""
    [green]Running interactive session[/]
        {SETTINGS_HEADER}
            [white]{{args}}[/]
"""

JUPYTER_WELCOME = """
    [hot]Started Jupyter Server!![/]

    [heading]Web browser access:[/]
        You'll need to set up an ssh tunnel. Open a new console
        and enter the tunnel script below.
        Then paste the browser url into your browser of choice!

    [heading]VS Code access:[/]
        Start a VS Code SSH session (see here for more info:
        https://code.visualstudio.com/docs/remote/ssh). Open your
        Jupyter notebook file, then set the Jupyter server to remote:
            Command Pallete > "Jupyter: Specify local or remote Jupyter server for
            connections"
        When prompted, enter the Server URL

    [heading]Tunnel script (replace <hostname> with your own hostname):[/]
        {tunnel_script}
    [heading]Browser URL:[/]
        {browser_url}
    [heading]Server URL:[/]
        {url}

    Once in the interactive shell, you can use kjupyter subcommands to interact with
    jupyter:
        - kjupyter log      View the server logs
        - kjupyter console  Start an interactive ipython console
        - kjupyter url      View the server url
        - kjupyter tunnel   Echo bash code to create an ssh tunnel to the server
"""
