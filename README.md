This project is in a draft state.

Utility functions to make working with SLURM easier. 

# Installation
Cluster utils is meant to be run in a SLURM environment, and thus will only install on linux. Open a shell and run the following command:

```
curl -sSL https://raw.githubusercontent.com/pvandyken/kslurm/master/install_kslurm.py | python -
```

If you wish to uninstall, run the same command with --uninstall added to the end.

# Features
Currently offers two commands:
* kbatch: for batch submission jobs (no immediate output)
* krun: for interactive submission

Both support a regex-based argument parsing, meaning that instead of writing a SLURM file or supplying confusing --command-arguments, you can request resources with an intuitive syntax:

```
krun 4 3:00 15G gpu 
```
This command will request interactive session with __4__ cores, for __3hr__, using __15GB__ of memory, and a gpu.

You could also add a command to run immediately:
```
krun jupyter-lab '$(hostname)' --no-browser
```

You can directly submit commands to kbatch without a script file:

```
kbatch 00:30 1000MB cp very/big/file.mp4 another/location
```

Both kbatch and krun default to 1 core, for 3hr, with 4G of memory.

You can also run a predefined job template using -j _template_. Run either command with -J to get a list of all templates. Any template values can be overriden simply by providing the appropriate argument.

