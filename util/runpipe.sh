#!/bin/bash

# Exit on any errors
# 2: path to tests
# TODO: specify pipechek home

set -e
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ] || [ -z "$7" ]
then
  echo "Usage: ./runpipe.sh <path to pipecheck> <path to tests> <list of tests> <path to uarch> <uarch name> <num threads>"
  exit 2
fi

# Store all of the tests in the given path into TESTS
TESTS=$(cat $3)
# OUTPUTDIR=results/graphs-herd-$5-$(date +"%m-%d-%y--%H-%M-%S-%p")/$7
OUTPUTDIR=results/$5/$7

mkdir -p $OUTPUTDIR
rm -f latest
ln -s $OUTPUTDIR latest
cp $1/pipecheck $OUTPUTDIR

# Loop over each test
date | tee $OUTPUTDIR/log.txt
parallel -j$6 --results $OUTPUTDIR time $OUTPUTDIR/pipecheck -i $2/{} -o $OUTPUTDIR/{}.gv -m $4/$5 ::: $TESTS 2>&1 | grep "Stricter|BUG" # >  out.txt # || true

echo "$0 Done!"
