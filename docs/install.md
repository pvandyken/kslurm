# Installation Guide

The recommend way to install kslurm is via [`pipx`](https://pypa.github.io/pipx), a tool for installing python applications.
This will make kslurm globally available without infecting your global python environment.
If you're not sure whether pipx is installed, run `pipx --version` and see if you get any output. If a version number prints, you can skip to step 2.

## Step 1: Install pipx

Start by activating either python 3.9 or 3.10. On most clusters, you'll run something like this:

```bash
module load python/3.10
```

If you get an error saying the specified version is not found, use the spider command:

```bash
module spider python
```

That should list the available python versions and give loading instructions. If the module command is not found, refer to your cluster documentation for software loading instructions. You can verify the correction python version is loaded by running

```bash
python --version
```

Once python is loaded, run the following to install pipx

```bash
pip install --user pipx
```

## Step 2: Install kslurm

Simply run

```bash
pipx install kslurm
```

````{warning}
Note that kslurm requires Python 3.9 or higher.
If pipx was installed using a lower version (e.g. 3.8), you will need to manually specify the python executable to use.
Activate the appropriate python version (e.g. `module load python/3.10`) so that when you run `python --version`, the correct version appears.
Then run

```bash
pipx install kslurm --python $(which python)
```
````

## Step 3: Activate bash features

For full kslurm features, including integration with `pip`, you need to source the init script, preferably in your `~.bash_profile` (the init script contains commands that may not be available on non-login nodes). You can do this by running:

```bash
kpy bash >> $HOME/.bash_profile
```

## Step 4: Configuration

Finally, you need to complete some basic configuration. First, set your SLURM account. Run

```bash
kslurm config account -i
```

This will begin an interactive session letting you choose from the accounts available to you. Each account will be listed with it's LevelFS. The higher the LevelFS, the more underused the account is, so prefer accounts with higher values.

Next, set your pipdir. This will be used to store python wheels and virtual envs. It should be in a permanent storage or project directory. For instance, on ComputeCanada servers, it should go in `$HOME/projects/<account_name>/<user_name>/.kslurm`. Use the following command:

```bash
kslurm config pipdir <dir>
```

## Upgrading and uninstalling

The app can be updated by running

```bash
pipx upgrade kslurm
```

and removed using

```bash
pipx uninstall kslurm
```

## Neuroglia-helpers Integration

See the [dedicated page](neuroglia-helpers.md).

## Legacy Installer

kslurm includes an installation script that, previously, was the recommended install method.
While it should technically still work, it is no longer supported and may be removed in the future.
Its instructions are included, for reference, below.

Users who previously installed kslurm via this script should switch to a pipx install for long term support. Simply uninstall `kslurm` using the instructions below, then install via pipx as described above

Installation is via the following command:

```bash
curl -sSL https://raw.githubusercontent.com/pvandyken/kslurm/master/install_kslurm.py | python -
```

If you wish to uninstall, run the same command with `--uninstall` added to the end.

The package can be updated by running `kslurm update`.
