# kpy

kpy bundles a set of commands to help manage pip virtual environments on Slurm compute clusters, specifically addressing a few issues unique to such servers:

## Ephemeral venvs

In most use cases, python venvs are installed on compute clusters, ideally on local scratch storage.
This makes venvs inherently ephemeral.
Because installing a venv can take an appreciable amount of time, kpy packs tools to archive entire venvs for storage in a permanent local repository (ideally located in project-specific or permanent storage). Once saved, venvs can be quickly reloaded into a new compute environment.

Note that copying venvs from one location to another is not a trivial task. The current setup has been tested on ComputeCanada servers without any issues so far, but problems may arise on another environment.

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
Call without a name to list the venvs you can activate.

### `list`

```bash
# usage
kpy list
```

List all saved venvs (i.e. venvs you can `load`)

### `rm`

```bash
# usage
kpy rm <name>
```

Delete a saved venv.

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
