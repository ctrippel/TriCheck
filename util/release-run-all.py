#!/usr/bin/env python

import itertools
import fileinput
import fnmatch
import glob
import os
import re
import subprocess
import sys, getopt


def runCheck(pipecheck_dir, ctests_dir, uarch_dir, models_list, num_threads):
  models = models_list.split(',')

  for uarch in models:
    for test_set in os.listdir(ctests_dir):
      # create tests.txt file for test_set
      if (os.path.isfile(ctests_dir + "/" + test_set + "/pipecheck/tests.txt")):
        os.remove(ctests_dir + "/" + test_set + "/pipecheck/tests.txt");
      subprocess.call("for i in " + ctests_dir + "/" + test_set + "/pipecheck/" + "*.test; do basename ${i} >> " + ctests_dir + "/" + test_set + "/pipecheck/" + "tests.txt; done", stderr=subprocess.STDOUT, shell=True);
   
      print "Running " + test_set + " tests..."

      runpipe01 = pipecheck_dir;			 		# path to tests
      runpipe02 = ctests_dir + "/" + test_set + "/pipecheck"; 		# path to tests
      runpipe03 = ctests_dir + "/" + test_set + "/pipecheck/tests.txt" 	# list of tests
      runpipe04 = uarch_dir 						# path to uarch
      runpipe05 = uarch 						# uarch model
      runpipe06 = num_threads 						# num threads
      runpipe07 = test_set 						# num threads
      
      runpipe_cmd = "./runpipe.sh " + runpipe01 + " " + runpipe02 + " " + runpipe03 + " " + runpipe04 + " " + runpipe05 + " " + runpipe06 + " " + runpipe07; 
      print runpipe_cmd;

      subprocess.call(runpipe_cmd, stderr=subprocess.STDOUT, shell=True)
    
def main(argv):
  usage_string = "usage: \t release-run-all.py [arguments] \
                 \n\nDescription: \tRun all tests in ctests/*/pipecheck/ directories on all specified uarches. \
                 \n\nArguments: \
                 \n\t-h or --help \t\t\t\t\t Display this help and exit \
                 \n\t-p or --pipecheck <pipecheck_dir> \t\t Must specify location of pipecheck executable \
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

  pipecheck_dir = ""

  # Try to parse opts
  try:
    opts, args = getopt.getopt(argv,"hp:c:u:m:t:",["help",
                                                 "pipecheck=",
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

    elif opt in ("-p", "--pipecheck"):
      pipecheck_dir = arg

    elif opt in ("-c", "--ctests"):
      ctests_dir = arg

    elif opt in ("-u", "--uarches"):
      uarch_dir = arg

    elif opt in ("-m", "--models"):
      models_list = arg

    elif opt in ("-t", "--threads"):
      num_threads = arg

  if not os.path.isdir(os.path.expanduser(pipecheck_dir)):
    print "ERROR: " + pipecheck_dir + " is not a valid path. Need to specify a pipecheck directory..."
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(ctests_dir)):
    print "ERROR: $TRICHECK_HOME/tests/ctests directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(uarch_dir)):
    print "ERROR: $TRICHECK_HOME/uarches directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  if os.listdir(uarch_dir) == []:
    print "ERROR: No files in " + uarch_dir + "\n"
    print usage_string;
    sys.exit(1);

  print 'pipecheck directory is "' + pipecheck_dir + '"'
  print 'C11 tests directory is "' + ctests_dir + '"'
  print 'Microarchitectures directory is "' + uarch_dir + '"'
  print 'List of specified models is "' + models_list + '"\n'

  runCheck(pipecheck_dir, ctests_dir, uarch_dir, models_list, str(num_threads))

if __name__ == "__main__":
   main(sys.argv[1:])
