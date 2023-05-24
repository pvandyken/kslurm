module load apptainer python/3

#light version doesn't display welcome message
if [ "$#" = 1 ]
then
	use_light=1
else
	use_light=0
fi

export NEUROGLIA_DIR=$(kslurm neuroglia-helpers --src-dir)
cfg_profile=$(kslurm config neuroglia_profile)

if [ "$use_light" = 0 ]; then
	echo "***"
	echo " Initializing neuroglia-helpers"
fi

#-------- this section always gets run -------

export PATH=${NEUROGLIA_DIR}/bin:$PATH
export NEUROGLIA_BASH_LIB=$NEUROGLIA_DIR/etc/bash_lib.sh

if [[ ! -e $NEUROGLIA_DIR/cfg/graham_$cfg_profile.cfg ]]; then
    echo "$cfg_profile not found, reverting to default"
    cfg_profile=""
fi
set -a
source $NEUROGLIA_DIR/cfg/graham_${cfg_profile}.cfg
set +a

#make SINGULARITY_DIR if it doesn't exist
if [ ! -e $SINGULARITY_DIR/bids-apps ]
then
	mkdir -p $SINGULARITY_DIR/bids-apps

	if [ ! "$?" = 0 -o ! -e $SINGULARITY_DIR ]
	then
		echo "neuroglia-helpers init error:  Unable to set local SINGULARITY_DIR to $SINGULARITY_DIR"
	fi

fi


#----------------------------------------------

if [ "$use_light" = 0 ]
then

echo " Container path: $SINGULARITY_DIR"
echo " Singularity options: $SINGULARITY_OPTS"
echo " Neuroglia container: $NEUROGLIA_URI"
echo " CPU account: $CC_COMPUTE_ALLOC"

#echo "- printGroupUsage currently disabled -"
$NEUROGLIA_DIR/etc/printGroupUsage ${CC_COMPUTE_ALLOC}_cpu

echo "***"

fi

unset cfg_profile
unset use_light

