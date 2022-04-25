Utility functions to make working with SLURM easier.

# Installation
The recommend way to install kslurm is via [`pipx`](https://pypa.github.io/pipx), a tool for installing python applications.
This will make kslurm globally available without infecting your global python environment.
Installation instructions for pipx can be found on their [website](https://pypa.github.io/pipx).
Once installed, simply run
```bash
pipx install kslurm
```

Note that kslurm requires Python 3.9 or higher.
If pipx was installed using a lower version (e.g. 3.8), you will need to manually specify the python executable to use.
Activate the appropriate python version (e.g. `module load python/3.10`) so that when you run `python --version`, the correct version appears.
Then run

```bash
pipx install kslurm --python $(which python)
```

The app can be updated by running
```bash
pipx upgrade kslurm
```

and removed using
```bash
pipx uninstall kslurm
```

## Legacy Installer
kslurm includes an installation script that, previously, was the recommended install method.
While it should technically still work, it is no longer supported and may be removed in the future.
Its instructions are included, for reference, below.

```{note}
Users who previously installed kslurm via this script should switch to a pipx install for long term support. Simply uninstall `kslurm` using the instructions below, then install via pipx as described above
```

Installation is via the following command:
```
curl -sSL https://raw.githubusercontent.com/pvandyken/kslurm/master/install_kslurm.py | python -
```

If you wish to uninstall, run the same command with `--uninstall` added to the end.

The package can be updated by running `kslurm update`.

# Features
Currently offers four commands:
* kbatch: for batch submission jobs (no immediate output)
* krun: for interactive submission
* kjupyter: for Jupyter sessions
* kpy: for python environment management

All three use a regex-based argument parsing, meaning that instead of writing a SLURM file or supplying confusing `--arguments`, you can request resources with an intuitive syntax:

```
krun 4 3:00 15G gpu
```
This command will request an interactive session with __4__ cores, for __3hr__, using __15GB__ of memory, and a __gpu__.

Anything not specfically requested will fall back to a default. For instance, by default the commands will request 3hr jobs using 1 core with 4GB of memory. You can also run a predefined job template using -j _template_. Run either command with -J to get a list of all templates. Any template values can be overriden simply by providing the appropriate argument.

The full list of possible requests, their syntaxes, and their defaults can be found at the bottom of the README.

## krun

krun is used for interactive sessions on the cluster. If you run krun all by itself, it will fire up an interactive session on the cluster:

```
krun
```
You'll notice the server name in your terminal prompt will be changed to the cluster assigned to you. To end the session, simply use the `exit` command.

You can also submit a specific program to run:

```
krun 1:00 1G python my_program.py
```
This will request a 1hr session with one core and 1 GB of memory. The output of the job will be displayed on the console. Note that your terminal will be tied to the job, so if you quit, or get disconnected, your job will end. (tmux can be used to help mitigate this, see this [tutorial from Yale](https://docs.ycrc.yale.edu/clusters-at-yale/guides/tmux/) for an excellent overview).

Note that you should never request more than the recommended amount of time for interactive jobs as specified by your cluster administrator. For ComputeCanada servers, you should never request more than 3 hr. If you do, you'll be placed in the general pool for resource assignment, and the job could take hours to start. Jobs of 3hr or less typically start in less than a minute.

## kbatch

Jobs that don't require monitoring of the output or immediate submission, or will run for more than three hours, should be submitted using `kbatch`. This command schedules the job, then returns control of the terminal. Output from the job will be placed in a file in your current working directory entitled `slurm-[jobid].out`.

Improving on `sbatch`, `kbatch` does not require a script file. You can directly submit a command:

```
kbatch 2-00:00 snakemake --profile slurm
```
This will schedule a 2 day job running snakemake.

Of course, complicated jobs can still be submitted using a script. Note that kbatch explictely specifies the resources it knows about in the command line. Command line args override `#SBATCH --directives` in the submit script, so at this time, you cannot use such directives to request resources unless they are not currently supported by kslurm. This may change in a future release.

## kjupyter

This command requests an interactive job running a jupyter server. As with krun, you should not request a job more than the recommended maximum time for your cluster (3hr for ComputeCanada). If you need more time than that, just request a new job when the old one expires.

You should not provide any extra command to kjupyter. Just supply whatever resources you wish to request.
```
kjupyter 32G 2
```
This will start a jupyter session with 32 GB of memory and 2 cores.

Note that the command will fail if there is no `jupyter-lab` executable on the `PATH`. Use `pip install jupyterlab` if it's not installed. Typically, you should do this within a Python environment using a tool of your choice (e.g. virtualenv).

# Unsupported SLURM args

Currently, the only way to supply arguments to SLURM beyond the items listed below is to list it as an `#SBATCH --directive` in a submission script. This only works with `kbatch`, not `krun` or `kjupyter`. A future release may support a method to supply these arguments directly on the command line. If you frequently use an option not listed below, make an issue and we can discuss adding support!

# Slurm Syntax

The full syntax is outlined below. You can always run a command with `-h` to get help.

| Resource  |           Syntax           |                                                                   Default |                                                    Description |
| :-------- | :------------------------: | ------------------------------------------------------------------------: | -------------------------------------------------------------: |
| Time      | [d-]dd:dd -> [days-]hh:mm  |                                                                       3hr |                                   The amount of time requested |
| CPUS      |     d -> just a number     |                                                                         1 |                                   The number of CPUs requested |
| Memory    |            d(G/M)[B] -> e.g. 4G, 500MB |                                                            4GB | The amount of memory requested |
| Account   | --account <_account name_> |                                                                           |                      The account under which to submit the job. A default account can be configured using `kslurm config account <account_name>` |
| GPU       |            gpu             |                                                                     False |                         Provide flag to request 1 GPU instance |
| Directory |  <_any valid directory_>   |                                                                        ./ | Change the current working directory before submitting the job |
| x11       |           --x11            |                                                                     False |                   Requests x11 forwarding for GUI applications |

# kpy

kpy bundles a set of commands to help manage pip virtual environments on Slurm compute clusters, specifically addressing a few issues unique to such servers:

## Ephemeral venvs
In most use cases, python venvs are installed on compute clusters, ideally on local scratch storage.
This makes venvs inherently ephemeral.
Because installing a venv can take an appreciable amount of time, kpy packs tools to archive entire venvs for storage in a permanent local repository (ideally located in project-specific or permanent storage). Once saved, venvs can be quickly reloaded into a new compute environment.

```{warning}
Copying venvs from one location to another is not a trivial task. The current setup has been tested on ComputeCanada servers without any issues so far, but problems may arise on another environment.
```

## No internet
Compute clusters often don't have an internet connection, limiting our install repertoire to locally available wheels.
With kpy, venvs can be created on a login node (using the available internet connection), then saved and loaded onto a compute node.
Kpy also includes some optional bash tools (see `kpy bash`), including a wrapper around pip that prevents it from accessing the internet on compute nodes, and connecting it with a local private wheelhouse.

## Commands
### `create`

```bash
# usage
kpy create [<version|3.x>] [<name>]
```

Create a new environment.
Name is optional; if not provided, a placeholder name will be created.
Version must be of the form `3.x` where x is any number (e.g `3.8`, `3.10`).
If provided, the corresponding python version will be used in the virtual env.
Note that an appropriate python executable must be somewhere on your path (e.g. for `3.8` -> `python3.8`).
If not provided, the python version used to install kslurm will be used.

If run on a login node, the env will be created in a `$TMPDIR`.
If run on a compute node, it will be created in `$SLURM_TMPDIR`.

### `save`

```bash
# usage
kpy save [-f] <name>
```

Save the venv to your permanent cache.
This requires setting `pipdir` in the kslurm config (see below).
By default, `save` will not oversave an existing cache, but `-f` can be included to override this behaviour.
If a new name is provided, it will be used to update the current venv name and prompt.

### `load`


```bash
# usage
kpy load [<name>] [--as <newname>]
```

Load a saved venv from the cache.
This command only works on a compute node (i.e. `$SLURM_TMPDIR` must be defined).
If a venv called `<name>` already exists, the command will fail, as each name can only be used once.
`--as <newname>` works around this by changing the name of the loaded venv (the name of the saved venv will remain the same)
Calling `load` without any `<name>` will print a list of current cached venvs.

### `activate`

```bash
# usage
kpy activate [<name>]
```

Activate venv initialized using `create` or `load`.
Name will be the same as the name appearing in the venv prompt (i.e. the name provided on initial loading or creation, through `--as`, or the last saved name).
This command only works on a compute node.
Venvs created on a login node cannot be directly activated using kpy.

### `list`

```bash
# usage
kpy list
```

List currently initialized venvs (i.e. venvs you can `activate`).
This command only works on a compute node.


### `bash`

```bash
# usage
kpy bash
```

Echos a line of bash script that can be added to your `.bashrc` file:

```bash
kpy bash >> $HOME/.bashrc
```

This adds a few features to your command line environment:

- **pip wrapper**: Adds a wrapper around pip that detects if you are on a login node when running `install`, `wheel`, or `download`. If not on a login node, the `--no-index` flag will be appended to the command, preventing the use of an internet connection.
- **wheelhouse management**: If `pipdir` is configured in the kslurm config, a wheelhouse will be created in your pip repository. Any wheels downloaded using `pip wheel` will be placed in that wheelhouse, and all wheels in the wheelhouse will be discoverable by `pip install`, both on login and compute nodes.

## Configuration

kslurm currently supports a few basic configuration values, and more will come with time. All configuration can be set using the command

```bash
kslurm config <key> <value>
```

You can print the value of a configuration using

```bash
kslurm config <key>
```

### Current values

* `account`: Default account to use for kslurm commands (e.g. `kbatch`, `krun`, etc)
* `pipdir`: Directory to store cached venvs and wheels. Should be a project or permanent storage dir.
