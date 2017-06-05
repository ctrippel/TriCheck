#!/usr/bin/env python

import itertools
import fileinput
import fnmatch
import glob
import os
import re
import subprocess
import sys, getopt


def genStats(results_dir, models_list):
  models = models_list.split(',')

  for uarch in models:
    fp_BUG = open(results_dir + '/' + uarch + "/BUG.txt", 'w+');
    fp_Strict = open(results_dir + '/' + uarch + "/Strict.txt", 'w+');

    for test_set in os.listdir(results_dir + '/' + uarch):
      if os.path.isdir(results_dir + '/' + uarch + '/' + test_set):
        try:
          t = subprocess.check_output('cat ' + results_dir + '/' + uarch + '/' + test_set + '/1/*/stdout | grep Strict', stderr=subprocess.STDOUT, shell=True)
          for i in (t.strip()).split("\n"):
            fp_Strict.write(uarch + '.' + test_set + ': ' + i + "\n")
        except:
          done = True

        try: 
          t = subprocess.check_output('cat ' + results_dir + '/'  + uarch + '/' + test_set + '/1/*/stdout | grep BUG', stderr=subprocess.STDOUT, shell=True)
          for i in (t.strip()).split("\n"):
            fp_BUG.write(uarch + '.' + test_set + ': ' + i + "\n")
        except:
          done = True

  fp_Strict.close()
  fp_BUG.close()

def main(argv):
  models_list = ""
  usage_string = "usage: \t release-stats.py [arguments] \
                 \n\nDescription: \tGenerate Bug and Strict log files. \
                 \n\nArguments: \
                 \n\t-h or --help \t\t\t\t\t Display this help and exit \
                 \n\t-r or --results <results_dir> \t\t\t Assumed to be $TRICHECK_HOME/util/results \
                 \n\t-m or --models <uarch0,uarch1,...,uarchN> \t Assumed to be all uarches with directories in $TRICHECK_HOME/util/results";


  # Check if TRICHECK_HOME exists
  if "TRICHECK_HOME" in os.environ:
    results_dir = os.environ['TRICHECK_HOME'] + "/util/results/";
  else:
    results_dir = ""

  # Try to parse opts
  try:
    opts, args = getopt.getopt(argv,"hr:m:",["help",
                                             "results=",
                                             "models="]);

  except getopt.GetoptError:
     print usage_string;
     sys.exit(1)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print usage_string;
      sys.exit()

    elif opt in ("-r", "--results"):
      results_dir = arg

    elif opt in ("-m", "--models"):
      models_list = arg


  if not os.path.isdir(results_dir):
    print "ERROR: $TRICHECK_HOME/util/results directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  elif (models_list == ""):
    models_list = ",".join(os.listdir(os.environ['TRICHECK_HOME'] + "/util/results/"));

  if os.listdir(results_dir) == []:
    print "ERROR: No files in " + results_dir + "\n"
    print usage_string;
    sys.exit(1);

  print 'Check results directory is "' + results_dir + '"'
  print 'List of specified models is "' + models_list + '"\n'

  genStats(results_dir, models_list)

if __name__ == "__main__":
   main(sys.argv[1:])










