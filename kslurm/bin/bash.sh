# vars that are cached:
# KSLURM_COMPUTE_NODES
# PIP_WHEEL_DIR

cache=~/.cache/kslurm/kpy_cache.sh
nodes=~/.cache/kslurm/kpy_cache.nodes

# resets the cache using the 'reset' arg
if [ "$#" -gt 0 ]
then
    if [ "$1" = "reset" -a -e "${cache}" ]
    then 
      echo "Resetting cache at $cache"
      rm -f $cache
    fi
fi

if [ -e "$cache" ]
then
  source $cache
else
  echo "#cache created on `date`" > $cache
  sinfo -N -h | awk '{print $1}' | sort -u > $nodes
  echo "export KSLURM_COMPUTE_NODES=\`cat $nodes\`" >> $cache

  if command -v kslurm &> /dev/null; then
    pipdir=$(kslurm config pipdir)
    if [[ -z $pipdir ]]; then
      echo "pipdir has not been defined. Please set a pipdir using \`kslurm config pipdir <directory>\`. Typically, this should be a directory in a project space or permanent storage directory."
    else
      wheelhouse="${pipdir%/}/wheels"
      if [[ ! -d "$wheelhouse" ]]; then
        mkdir -p "$wheelhouse"
      fi
      echo "export PIP_WHEEL_DIR=$wheelhouse" >> $cache
    fi
  else
    echo "kslurm program was not found on \$PATH. If installed in a virtualenv, be sure the env is activated."
  fi
fi



pip () {
  local installing installtype cmd wheelhouse
  [[ $1 == install || $1 == uninstall ]] && installing=1 || installing=
  [[ $1 == install || $1 == wheel || $1 == download ]] && installtype=1 || installtype=
  cmd=$1
  if [[ $KSLURM_COMPUTE_NODES =~ $(hostname) && -n $installtype ]]; then
    cmd="$cmd --no-index"
  fi

  if [[ -n $installtype ]]; then
    cmd="$cmd --find-links=$PIP_WHEEL_DIR"
  fi

  shift
  command pip $cmd $@
  if [[ -n $installing ]]; then
    for hook in "${KSLURM_POST_INSTALL_HOOKS[@]}"; do eval "$hook"; done
  fi
}
