_kpy_update_prompt() {
    if command -v kpy &> /dev/null; then
      local newname=$(kpy _refresh)
      if [[ -z "${VIRTUAL_ENV_DISABLE_PROMPT-}" && -n "${newname}" ]]; then
        export PS1="($newname) ${_OLD_VIRTUAL_PS1-}"
      fi
    fi
}

kpy () {
    if [[ $1 == load || $1 == activate || $1 == create ]]; then
      IFS='|'
      local cmd ret tmp
      tmp=${TMPDIR:-/tmp}
      cmd=$(mktemp "${tmp%/}/kslurm-$(basename $0).XXXXXXXXXX")
      command kpy $@ --script $cmd
      ret=$?
      if [[ $ret == 2 ]]; then
        source $cmd
        ret=0
      fi
      rm $cmd
      unset IFS

      return $ret
    elif [[ $1 == save ]]; then
      command kpy $@
      _kpy_update_prompt
    else
      command kpy $@
    fi
}
