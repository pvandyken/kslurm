[[ -e $HOME/.bashrc ]] && . $HOME/.bashrc
. $activate_path
unset activate_path
deactivate () { exit 0 &> /dev/null; }
_pip_prompt_refresh () {
    if command -v kpy &> /dev/null; then
      kpy _refresh
    fi;
}
KSLURM_POST_INSTALL_HOOKS["${#KSLURM_POST_INSTALL_HOOKS[@]}"]="_pip_prompt_refresh"
