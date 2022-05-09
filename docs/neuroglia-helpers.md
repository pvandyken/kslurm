# Neuroglia Helpers

[Neuroglia-helpers](https://github.com/khanlab/neuroglia-helpers) is the current definitive home for khanlab scripts. It's features are slowly being ported into kslurm, but the entire library remains accessible via `kslurm` to maintain feature access and for backwards-compatibility.

The neuroglia-helpers version bundled with kslurm is only tested to work on Compute Canada servers. However, it *may* work on any arbitary compute cluster if account names start with `def_`, if scratch directories are mounted as `/scratch/<user>`, and if a project directory is available via `$HOME/projects/<account>`.

## Initializing

Run the following command to source the initialization script in your `.bash_profile`.

```bash
kslurm neuroglia-helpers >> $HOME/.bash_profile
```

Members of the khanlab accounts should set the appropriate profile in their kslurm config:

```bash
kslurm config neuroglia_profile khanlab
```

A full list of profile files can be found [here](https://github.com/khanlab/neuroglia-helpers/tree/master/cfg). The files are named as `graham_<profile_name>.cfg`, so to use `graham_lpalaniy.cfg`, you should run `kslurm config neuroglia_profile lpalaniy`.

Once completed the above steps, login into the cluster again (or run `bash -l`), and everything should be completed. For complete neuroglia-helpers documetation, refer to the [github repository](https://github.com/khanlab/neuroglia-helpers).
