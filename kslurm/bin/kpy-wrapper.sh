kpy () {
    if [[ $1 == load || $1 == activate || $1 == create ]]; then
      IFS='|'
      local cmd ret tmp
      tmp=${TMPDIR:-/tmp}
      cmd=$(mktemp "${tmp%/}/kslurm-$(basename $0).XXXXXXXXXX")
      command kpy $@ --script $cmd
      ret=$?
      if [[ $ret == 2 ]]; then
        eval $(cat $cmd)
        ret=0
      fi
      rm $cmd
      unset IFS

      return $ret
    else
      command kpy $@
    fi
}
