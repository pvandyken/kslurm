from __future__ import absolute_import

import subprocess
from typing import Union

import kslurm.text as txt
from kslurm.args.command import command
from kslurm.exceptions import TemplateError
from kslurm.models import SlurmModel
from kslurm.slurm import SlurmCommand


@command
def krun(args: Union[SlurmModel, TemplateError]):
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
    slurm = SlurmCommand(args)
    if slurm.command:
        print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))
    else:
        print(txt.INTERACTIVE_MSG.format(args=slurm.slurm_args))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)
