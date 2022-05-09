# kapp

Kapp provides a set of tools to manage singularity containers. Pull images from docker hub without worring about image size, pulling the same image twice, or tracking whether your ":latest" image is up to date. Kapp manages your `.sif` image files so you can run them from anywhere on the cluster, without managing environment variables or remembering paths. Kapp managed images can be seamlessly consumed by snakemake workflows using the provided `--singularity-prefix` directory.

## `pull`

```bash
# usage
kapp pull <image_uri> [-a <alias>] [--mem <memory>]
```

Pull an image from a repository. Currently, only docker-hub is supported. The image uri should look like this:

```bash
[<scheme>://][<organization>/]<repo>:<tag>

# examples
docker://ubuntu:latest
nipreps/fmriprep:21.0.2
busybox:latest
```

Note that the scheme is optional, and defaults to `docker`. The organization should be omitted for official docker images.

When you call `kapp pull`, the tag gets resolved to the specific container it points to. Thus, if you pull multiple tags pointing to the same container (e.g. `:latest` and its associated version tag), the container will only be pulled once. Plus, if tags get updated (e.g. `:latest` when a new release comes out), `kapp pull` will download the latest version of the tag, even if you've pulled that tag before.

When pulling a container, you can use `-a <alias>` to set an alias for the uri. This alias can be used in place of the uri in future kapp commands (except for `kapp pull`). For instance, you could download fmriprep and run it using the following:

```bash
kapp pull nipreps/fmriprep:latest -a fmriprep
kapp run fmriprep
```

Building `.sif` files from docker containers can consume a significant amount of memory and resources, making an unsuitable operation for login nodes. kapp works around this by first downloading the container on the login node, then scheduling a build step on an interactive compute node. It will automatically try to estimate how much memory will be needed, but if a build fails due to lack of memory, you can specify how much memory to request using the `--mem <memory>` parameter. Note that very small containers will be built directly on the login node without a compute step.

## `path`
```bash
# usage
kapp path <uri_or_alias>
```

Prints the path of the specified container. This creates an easy way to use kapp managed containers with any arbitrary singularity command:

```bash
singularity -b /path/to/bind/dir $(kapp path my_container)
```

## `image`

```bash
# usage
kapp image (list|rm <uri_or_alias>)
```

Has two subcommands `list` and `rm <container>` to list all pulled containers and remove a container.

`kapp image rm` does not actually remove any data, it just removes the supplied uri (along with any aliases that point to it). This is because the underlying data may be used by other image tags. Dangling containers, which aren't pointed to by any local uris, can be deleted using `kapp purge dangling`

## `purge`

```bash
# usage
kapp purge dangling
```

Delete all dangling image files: i.e. files that aren't pointed to by any local uris. This command also removes any snakemake aliases pointing to the data.

## `alias`

```bash
# usage
kapp alias list
```

List all aliases currently in use, along with the containers they point to.

## `exec`, `shell`, `run`

```bash
# usage
kapp (exec|shell|run) <uri_or_alias> [args...]
```

Simple wrapper around `singularity (exec|shell|run)`. No singularity args can be specified, only args for the container. If you need to specify singularity args, call singularity directly and use `kapp path <container>` to get the container path. Note that most singularity args (e.g. directory bids) can be specified using environment variable, and such variables will be consumed by `kapp` as normal.

## `snakemake`

Prints the path to the snakemake directory. This path can be supplied to the snakemake parameter `--singularity-prefix`, allowing snakemake to seamlessly consume containers downloaded using kapp. This is especially usefull for cluster execution without internet connection: containers can be pulled in advance on a login node, then used by snakemake later.
