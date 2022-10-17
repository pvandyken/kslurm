if [[ -z $_skiprc ]]; then
  [[ -e $HOME/.bashrc ]] && . $HOME/.bashrc
else
  unset $_skiprc
fi

. $activate_path
unset activate_path

if [[ -n $kpy_set_subshell ]]; then
  export KSLURM_KPY_SUBSHELL=1
fi
unset kpy_set_subshell

if [[ -n $KSLURM_KPY_SUBSHELL ]]; then
  deactivate () { exit 0 &> /dev/null; }
fi


if [[ $(type -t kpy) != 'function' ]]; then
  source $(kpy _kpy_wrapper)
fi


if [[ ! " ${KSLURM_POST_INSTALL_HOOKS[*]} " =~ " _kpy_update_prompt " ]]; then
  KSLURM_POST_INSTALL_HOOKS["${#KSLURM_POST_INSTALL_HOOKS[@]}"]="_kpy_update_prompt"
fi
