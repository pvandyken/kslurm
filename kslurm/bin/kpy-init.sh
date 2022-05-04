[[ -e $HOME/.bashrc ]] && . $HOME/.bashrc

. $activate_path
unset activate_path

if [[ -n $kpy_set_subshell ]]; then
  export KSLURM_KPY_SUBSHELL=1
fi
unset kpy_set_subshell

if [[ -n $KSLURM_KPY_SUBSHELL ]]; then
  deactivate () { exit 0 &> /dev/null; }
fi

_pip_prompt_refresh () {
    if command -v kpy &> /dev/null; then
      kpy _refresh
    fi;
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

if [[ ! " ${KSLURM_POST_INSTALL_HOOKS[*]} " =~ " _pip_prompt_refresh " ]]; then
  KSLURM_POST_INSTALL_HOOKS["${#KSLURM_POST_INSTALL_HOOKS[@]}"]="_pip_prompt_refresh"
fi
