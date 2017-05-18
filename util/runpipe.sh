#!/bin/bash

# Exit on any errors
# 1: path to tests
# TODO: specify pipechek home

set -e
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ]
then
  echo "Usage: ./runpipe.sh <path to tests> <list of tests> <uarch name> <num threads> <test name> <path to uarch>"
  exit 1
fi

# Store all of the tests in the given path into TESTS
TESTS=$(cat $2)
# OUTPUTDIR=results/graphs-herd-$4-$(date +"%m-%d-%y--%H-%M-%S-%p")/$6
OUTPUTDIR=results/$4/$6

mkdir -p $OUTPUTDIR
rm -f latest
ln -s $OUTPUTDIR latest
cp ~/mcm_verify/PipeCheck/src/pipecheck $OUTPUTDIR

# Loop over each test
date | tee $OUTPUTDIR/log.txt
parallel -j$5 --results $OUTPUTDIR time $OUTPUTDIR/pipecheck -i $1/{} -o $OUTPUTDIR/{}.gv -m $3/$4 ::: $TESTS 2>&1 | grep "Stricter|BUG" # >  out.txt # || true

echo "$0 Done!"
