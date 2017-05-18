#!/usr/bin/env python

import itertools
import fileinput
import fnmatch
import glob
import os
import re
import subprocess
import path
import sys, getopt


def runCheck(ctests_dir, uarch_dir, models_list, num_threads):
  models = models_list.split(',')

  for uarch in models:
    for test_set in os.listdir(ctests_dir):
      # create tests.txt file for test_set
      if (os.path.isfile(ctests_dir + "/" + test_set + "/pipecheck/tests.txt")):
        os.remove(ctests_dir + "/" + test_set + "/pipecheck/tests.txt");
      subprocess.call("for i in " + ctests_dir + "/" + test_set + "/pipecheck/" + "*.test; do basename ${i} >> " + ctests_dir + "/" + test_set + "/pipecheck/" + "tests.txt; done", stderr=subprocess.STDOUT, shell=True);
   
      print "Running " + test_set + " tests..."

      runpipe01 = ctests_dir + "/" + test_set + "/pipecheck"; 		# path to tests
      runpipe02 = ctests_dir + "/" + test_set + "/pipecheck/tests.txt" 	# list of tests
      runpipe03 = uarch_dir 						# path to uarch
      runpipe04 = uarch 						# uarch model
      runpipe05 = num_threads 						# num threads
      runpipe06 = test_set 						# num threads
      
      runpipe_cmd = "./runpipe.sh " + runpipe01 + " " + runpipe02 + " " + runpipe03 + " " + runpipe04 + " " + runpipe05 + " " + runpipe06; 
      print runpipe_cmd;

      subprocess.call(runpipe_cmd, stderr=subprocess.STDOUT, shell=True)
    
def main(argv):
  usage_string = "usage: \t release-run-all.py [arguments] \
                 \n\nDescription: \tRun all tests in ctests/*/pipecheck/ directories on all specified uarches. \
                 \n\nArguments: \
                 \n\t-h or --help \t\t\t\t\t Display this help and exit \
                 \n\t-c or --ctests <ctests_dir> \t\t\t Assumed to be $TRICHECK_HOME/tests/ctests \
                 \n\t-u or --uarches <uarches_dir> \t\t\t Assumed to be $TRICHECK_HOME/uarches \
                 \n\t-m or --models <uarch0,uarch1,...,uarchN> \t Assumed to be all uarches in $TRICHECK_HOME/uarches \
                 \n\t-t or --threads <num_threads> \t\t\t Default is 2";

  num_threads = 2

  # Check if TRICHECK_HOME exists
  if "TRICHECK_HOME" in os.environ:
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests";
    uarch_dir = os.environ['TRICHECK_HOME'] + "/uarches/";
    models_list = ",".join(os.listdir(os.environ['TRICHECK_HOME'] + "/uarches/"));
  else:
    ctests_dir = ""
    uarch_dir = ""
    models_list = ""

  # Try to parse opts
  try:
    opts, args = getopt.getopt(argv,"hc:u:m:t:",["help",
                                                 "ctests=",
                                                 "uarches=",
                                                 "models=",
                                                 "threads="]);

  except getopt.GetoptError:
     print usage_string;
     sys.exit(1)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print usage_string;
      sys.exit()

    elif opt in ("-c", "--ctests"):
      ctests_dir = arg

    elif opt in ("-u", "--uarches"):
      uarch_dir = arg

    elif opt in ("-m", "--models"):
      models_list = arg

    elif opt in ("-t", "--threads"):
      num_threads = arg

  if not os.path.isdir(ctests_dir):
    print "ERROR: $TRICHECK_HOME/tests/ctests directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(uarch_dir):
    print "ERROR: $TRICHECK_HOME/uarches directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  if os.listdir(uarch_dir) == []:
    print "ERROR: No files in " + uarch_dir + "\n"
    print usage_string;
    sys.exit(1);

  print 'C11 tests directory is "' + ctests_dir + '"'
  print 'Microarchitectures directory is "' + uarch_dir + '"'
  print 'List of specified models is "' + models_list + '"\n'

  runCheck(ctests_dir, uarch_dir, models_list, str(num_threads))

if __name__ == "__main__":
   main(sys.argv[1:])

