# Requesting Jobs

kslurm has three commmands for requesting jobs:

* kbatch: for batch submission jobs (no immediate output)
* krun: for interactive submission
* kjupyter: for Jupyter sessions

All three use a regex-based argument parsing, meaning that instead of writing a SLURM file or typing out confusing `--arguments`, you can request resources with an intuitive syntax:

```bash
krun 4 3:00 15G gpu
```

This command will request an interactive session with __4__ cores, for __3hr__, using __15GB__ of memory, and a __gpu__.

Anything not specfically requested will fall back to a default. For instance, by default the commands will request 3hr jobs using 1 core with 4GB of memory. You can also run a predefined job template using -j _template_. Run either command with -J to get a list of all templates. Any template values can be overriden simply by providing the appropriate argument.

The full list of possible requests, their syntaxes, and their defaults can be found at the bottom of the README.

## krun

krun is used for interactive sessions on the cluster. If you run krun all by itself, it will fire up an interactive session on the cluster:

```bash
krun
```

You'll notice the server name in your terminal prompt will be changed to the cluster assigned to you. To end the session, simply use the `exit` command.

You can also submit a specific program to run:

```bash
krun 1:00 1G python my_program.py
```

This will request a 1hr session with one core and 1 GB of memory. The output of the job will be displayed on the console. Note that your terminal will be tied to the job, so if you quit, or get disconnected, your job will end. (tmux can be used to help mitigate this, see this [tutorial from Yale](https://docs.ycrc.yale.edu/clusters-at-yale/guides/tmux/) for an excellent overview).

Note that you should never request more than the recommended amount of time for interactive jobs as specified by your cluster administrator. For ComputeCanada servers, you should never request more than 3 hr. If you do, you'll be placed in the general pool for resource assignment, and the job could take hours to start. Jobs of 3hr or less typically start in less than a minute.

!!! note
    Internally, `krun` wraps two different slurm commands. When no command or program is specified, krun uses `salloc` to start a new interactive session. When used with a program, it calls `srun`. The difference becomes noticable when running `krun` on a compute node: running a simple `krun` will request a new job allocation and possibly switch you to a different node. Running `krun <command>` will run the command on the current allocation.

## kbatch

Jobs that don't require monitoring of the output or immediate submission, or will run for more than three hours, should be submitted using `kbatch`. This command schedules the job, then returns control of the terminal. Output from the job will be placed in a file in your current working directory entitled `slurm-[jobid].out`.

Improving on `sbatch`, `kbatch` does not require a script file. You can directly submit a command:

```bash
kbatch 2-00:00 snakemake --profile slurm
```

This will schedule a 2 day job running snakemake.

Of course, complicated jobs can still be submitted using a script. Note that kbatch explictely specifies the resources it knows about in the command line. Command line args override `#SBATCH --directives` in the submit script, so at this time, you cannot use such directives to request resources unless they are not currently supported by kslurm. This may change in a future release.

## kjupyter

This command requests an interactive job running a jupyter server. As with krun, you should not request a job more than the recommended maximum time for your cluster (3hr for ComputeCanada). If you need more time than that, just request a new job when the old one expires.

In addition to the desired resources, you should use the `--venv` flag to request a saved virtual environment (see `kpy save`). Jupyter will be started in whatever environment you request. `jupyter-lab` should already be installed in the venv.

```bash
kjupyter 32G 2 --venv <your_venv_name>
```

This will start a jupyter session with 32 GB of memory and 2 cores.

If no venv is specified, `kjupyter` will assume that the `jupyter-lab` command is already available on the `$PATH`. This is useful to run a global instance of jupyter, or jupyter installed in an active venv. Note that this prevents installing jupyter on local scratch, so performance will take a hit.

## Unsupported SLURM args

Any slurm argument can be given to any of the above commands, and it will be transparently passed on to the underlying command. Specifically, any unrecognized argument beginning with one or two dashes (e.g. `-A`, `--ntasks`) will be passed on to slurm. There are just two restrictions:

1. Any arguments taking parameters must be provided as a single word. For long-form arguments with a double dash prefix, this means putting a equal sign (`=`) between the argument and the parameter (e.g. `--output=<filename_pattern>`). For short-form arguments with a single dash prefix, the parameter should immediately follow the argument with no space (e.g. `-o<filename_patthern>`). kslurm will not recognize any parameters seperated from their argument by a space (e.g. `--output <filename_pattern>` and `-o <filename>` will _not_ work properly).

2. A few short-form arguments (e.g. `-J`, `-j`, `-l`) have their own kslurm definitions and can not be passed on to slurm. Use the long-form arguments instead.

## Slurm Syntax

The full syntax is outlined below. You can always run a command with `-h` to get help.

| Resource  |           Syntax           |                                                                   Default |                                                    Description |
| :-------- | :------------------------: | ------------------------------------------------------------------------: | -------------------------------------------------------------: |
| Time      | [d-]dd:dd -> [days-]hh:mm  |                                                                       3hr |                                   The amount of time requested |
| CPUS      |     d -> just a number     |                                                                         1 |                                   The number of CPUs requested |
| Memory    |            d\(G/M)[B] -> e.g. 4G, 500MB |                                                            4GB | The amount of memory requested |
| Account   | --account <_account name_> |                                                                           |                      The account under which to submit the job. A default account can be configured using `kslurm config account <account_name>` |
| GPU       |            gpu             |                                                                     False |                         Provide flag to request 1 GPU instance |
| Directory |  <_any valid directory_>   |                                                                        ./ | Change the current working directory before submitting the job |
| x11       |           --x11            |                                                                     False |                   Requests x11 forwarding for GUI applications |
