from typing import List
import sys, subprocess
from kslurm.slurm import SlurmCommand
from kslurm.models import SlurmModel
from kslurm.args import print_help
from .. import text as txt



def kjupyter(script: str, args: List[str]):
    """Start a Jupyter session
    
    Begins a Jupyter session on an interactive node. By default, it requests 3hr. No
    more time than this should be requested, as this could significantly delay the 
    start of the server.  
    
    For the command to work, a virtualenv containing jupyter-lab should already be
    activated. Use `pip install jupyter-lab`
    """
    slurm = SlurmCommand(sys.argv[1:], SlurmModel())
    if slurm.help:
        print_help(sys.argv[0], SlurmModel(), krun.__doc__) # type: ignore
        exit()
    
    slurm.command = ['jupyter-lab', "'$(hostname -f)'", "--no-browser"]
    print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

def main():
    kjupyter(sys.argv[0], sys.argv[1:])