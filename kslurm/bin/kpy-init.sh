[[ -e $HOME/.bashrc ]] && . $HOME/.bashrc
. $activate_path
unset activate_path
deactivate () { exit 0; }
