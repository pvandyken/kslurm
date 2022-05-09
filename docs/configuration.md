# Configuration

kslurm currently supports a few basic configuration values, and more will come with time. All configuration can be set using the command

```bash
kslurm config <key> <value>
```

You can print the value of a configuration using

```bash
kslurm config <key>
```

## Current values

- `account`: Default account to use for kslurm commands (e.g. `kbatch`, `krun`, etc)
- `pipdir`: Directory to store cached venvs and wheels. Should be a project or permanent storage dir.
