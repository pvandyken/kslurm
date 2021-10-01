from __future__ import absolute_import

from colorama import Fore

SETTINGS_HEADER = f"{Fore.LIGHTBLUE_EX}SETTINGS{Fore.RESET}"
COMMAND_HEADER = f"{Fore.LIGHTBLUE_EX}COMMAND{Fore.RESET}"

KBATCH_MSG = f"""
    {Fore.GREEN}Scheduling Batch Command
        {SETTINGS_HEADER}
            {Fore.WHITE}{{slurm_args}}
        {COMMAND_HEADER}
            {Fore.WHITE}{{command}}
"""

KRUN_CMD_MESSAGE = f""" \
    {Fore.GREEN}Running job
        {SETTINGS_HEADER}
            {Fore.WHITE} {{args}}
        {COMMAND_HEADER}
            {{command}}
"""

INTERACTIVE_MSG = f"""
    {Fore.GREEN}Running interactive session
        {SETTINGS_HEADER}
            {Fore.WHITE} {{args}}
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

    [heading]Tunnel script (replace <address> with your own address):[/]
        ssh -L {port}:{domain}:{port} <username@sub.domain.ext>
    [heading]Browser URL:[/]
        http://localhost:{port}{path}
    [heading]Server URL:[/]
        {url}

    Press Ctrl+C to exit the server
"""
