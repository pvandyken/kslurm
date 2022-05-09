# Home

kslurm is a high-performance assistant for slurm-powered compute clusters. It simplifies job requests, manages python environments, and makes your cluster workflow smooth and efficient.

kslurm provides:

* Intuitive, uniform commands to schedule batch jobs, request interactive sessions, and fire up jupyter notebooks

* Tools for python venv management specially adapted for cluster life.

## Installation

kslurm is best installed through pipx:

```bash
pipx install kslurm
```

After installing, use

```bash
kpy bash >> $HOME/.bash_profile
```

To initialize bash integrations.

See [here](install.md) for a detailed installation guide.

## Job requests

Slurm provides a very powerful interface for compute cluster job scheduling, most of which is unnecessary for daily computing needs. kslurm simplifies these commands into an intuitive syntax.

Consider the following examples:

### Interactive console

This can be requested with slurm using the `salloc` command. Often, you'll need to request extra memory and time, unless your goal is very minimal:

```bash
salloc --mem=4G --time=3:00:00 --account def-account
```

kslurm uses 4G of memory and a 3hr runtime as the default, so the above command becomes:

```bash
krun
```

### Running a specific command interactively

Typically you'd use `srun` to achieve this. In kslurm, the same command `krun` is used both for requesting an open interactive console and for running a specific job interactly:

```bash
krun python my-script.py
```

!!! note
    Specifically, with no command provided, krun uses salloc, but uses srun when a command is given.

### Requesting more resources

slurm resources are specified via traditional command line keywords: `--mem=<num>` for memory, `--cpus-per-task=<num>` for cpus, and so forth. kslurm uses a pattern matching syntax that lets you specificy runtime, memory, and number of cpus, the three most common resources, in a flash.

For example, memory is specified as a number plus a unit, e.g. `5G`, `300MB`, `60G`:

```bash
krun 16G
```

cpus is a simple number with no unit, e.g. `4`, `32`, `16`:

```bash
krun 16G 4
```

Runtime is requested as `hh:mm` or `days-hh:mm`, e.g. `4:00`, `12:00`, `4-00:00`

```bash
krun 16G 4 2:00
```

The above command starts an interactive session with 16G of memory and 4 cores, with a runtime of 2hr.

!!! warning
    Interactive sessions are not intended to be used for long running jobs, e.g. jobs running longer than 3 hrs. For these, jobs should be scheduled (see below). Check your organizational policies for specific length guidelines.

### Scheduling a longer job

Most jobs on the cluster are submitted to the scheduler via `sbatch`. This command typically requires you to write a bash script containing the commands. While this is still appropriate for complex, multistep jobs, it's overkill for single-process programs with long runtimes, such as those commonly used in neuroimaging analysis (e.g. running freesurfer). For these applications, kslurm provides kbatch:

```bash
kbatch 12:00 16 24G recon-all <recon-all-args>
```

The above command schedules a 12hr job with 16 cores and 24G of memory. Once started, the job will run recon-all.

### Other slurm args?

`sbatch`, `srun`, and `salloc` are highly configurable, each with a long list of available args. While most of these don't have kslurm counterparts, `krun` and `kbatch` will still accept slurm arguments and pass them on to the respective slurm command.

## Python environments

Compute environments present a few unique challenges to python environment management:

* Central venv management in the home directory is prevented by space limitations (e.g. most clusters discourage the use of anaconda)

* The most performant location to install venvs is the local scratch dir of a compute node, but these directories are deleted as soon as the job finishes. `requirements.txt` files help with reproducibility, but it takes a few minutes to install a venv from scratch, a delay especially annoying for interactive work.

* Compute nodes often don't have internet connection, so installing any arbitrary package from the pip index is not possible.

kslurm addresses these problems through `kpy`, a set of commands to save and reload entire vitual environments as tar files. A venv can be composed on a login node, using the available internet, then saved and reloaded as needed on a login node.
