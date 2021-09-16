import sys, subprocess
from colorama import Fore
from pathlib import Path
from kslurm.slurm import SlurmCommand, ArgList
from kslurm.args import print_help
from . import text as txt

def kbatch():
    """Submit a job using sbatch

    Supports scripts (e.g. ./script.sh) or direct commands (e.g. cp dir/file.txt dir2)

    When your command contains bash interpreted elements such as $VARIABLES and 
    $(subshells), these will be immediately expanded. Normally, this behaviour
    is fine, but sometimes they should only be interpretted on the allocated cluster.
    For instance, $SLURM_TMPDIR will evaluate to "" unless it is interpretted later.
    To force this behaviour, wrap the $VARIABLE or $(subshell) in quotes:
        '$SLURM_TMPDIR'
        '$(hostname)'
    """

    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.help:
        print_help(sys.argv[0], ArgList(), kbatch.__doc__) # type: ignore
        exit()
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(txt.KBATCH_MSG.format(slurm_args=slurm.slurm_args, command=command))
    if slurm.command:
        output = subprocess\
            .run(slurm.batch, shell=True, capture_output=True)\
            .stdout.decode()

        if slurm.test:
            # output will be the issued command, so we print it
            print(Fore.WHITE + output)
        else:
            # We subtract the last character of the output
            # to remove the final "\n" character and get the 
            # job_id
            slurmid = output[:-1]

            print(f"""Scheduled job {slurmid}.
    To cancel, run:
        scancel {slurmid}
        """)

def krun():
    """Start an interactive session
    
    If no command is provided, an interactive session will begin. The server name
    on your shell prompt will change to the name of your cluster, and you can
    run any job you wish from there. To exit the session, enter "exit".
    
    If a command is provided, it will be immediately submitted using srun. The output 
    of the command will be displayed on the console. 
    
    Using this command, jobs will begin much quicker than sbatch, however, it should
    only be used for interactive sessions. Note that you should request jobs no longer
    than 3hr. Anything longer, and it could take a very long time for the job to begin.

    When your command contains bash interpreted elements such as $VARIABLES and 
    $(subshells), these will be immediately expanded. Normally, this behaviour
    is fine, but sometimes they should only be interpretted on the allocated cluster.
    For instance, $SLURM_TMPDIR will evaluate to "" unless it is interpretted later.
    To force this behaviour, wrap the $VARIABLE or $(subshell) in quotes:
        '$SLURM_TMPDIR'
        '$(hostname)'
    """
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.help:
        print_help(sys.argv[0], ArgList(), krun.__doc__) # type: ignore
        exit()
    if slurm.command:
        print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))
    else:
        print(txt.INTERACTIVE_MSG.format(args=slurm.slurm_args))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

def kjupyter():
    """Start a Jupyter session
    
    Begins a Jupyter session on an interactive node. By default, it requests 3hr. No
    more time than this should be requested, as this could significantly delay the 
    start of the server.  
    
    For the command to work, a virtualenv containing jupyter-lab should already be
    activated. Use `pip install jupyter-lab`
    """
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.help:
        print_help(sys.argv[0], ArgList(), krun.__doc__) # type: ignore
        exit()
    
    slurm.command = ['jupyter-lab', "'$(hostname -f)'", "--no-browser"]
    print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

def install_library() -> None:
    print("Checking for Updates")
    python = Path.home().joinpath(".local/share/kutils/venv/bin/python")
    specification = "git+https://github.com/pvandyken/kslurm.git"

    subprocess.run(
        [str(python), "-m", "pip", "install", specification],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )