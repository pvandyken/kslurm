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