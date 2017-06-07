#!/usr/bin/env python

import sys
import os
import subprocess
import tempfile
import re
import fnmatch
import sys, getopt

def genISATests(ctests_dir, TriCheck_dir, herd_dir):
  for dir in os.listdir(ctests_dir):
    if not os.path.isdir(ctests_dir + dir + '/pipecheck'):
      os.makedirs(ctests_dir + dir + "/pipecheck");
    else:
      print "Skipping " + dir + " tests because " + dir + "/pipecheck exists..."
      continue;
  

    print "Running cpp_herd_to_pipecheck.py for " + dir + " tests..."
    for file in os.listdir(ctests_dir + dir):
      if (fnmatch.fnmatch(file, '*.litmus')):

        #print herd_dir + "/cpp_herd_to_pipecheck.py " + herd_dir + "/c11_partialSC.cat " + ctests_dir + dir + "/" + file + " /dev/null " + herd_dir + "/sc.cat all"
        os.system(herd_dir + "/cpp_herd_to_pipecheck.py " + herd_dir + "/c11_partialSC.cat " + ctests_dir + dir + "/" + file + " /dev/null " + herd_dir + "/sc.cat all");
 
    subprocess.call("for i in ../tests/ctests/" + dir + "/*.test; do mv ${i} ../tests/ctests/" + dir + "/pipecheck/; done", stderr=subprocess.STDOUT, shell=True);
  
# Main function
# Parse command line
# Call getISATests
def main(argv):
  usage_string = "usage: \t 02-release-batch-cpp-herd-to-pipecheck.py [arguments] \
                  \n\nDescription: \tCreate a corresponding ISA litmus tests for each C11 atomic litmus test. \
                                   \n\t\tAny ISA fence mappings will be generated later \
                  \n\nArguments: \
                  \n\t-h or --help \t\t\t\t Display this help and exit \
                  \n\t-T or --TriCheck <TriCheck_dir> \t Assumed to be $TRICHECK_HOME \
                  \n\t-H or --herd <herd_dir> \t Assumed to be $TRICHECK_HOME/herd \
                  \n\t-c or --ctests <ctests_dir> \t\t Assumed to be $TRICHECK_HOME/tests/ctests";

  # Check if TRICHECK_HOME environment variable has been set
  if "TRICHECK_HOME" in os.environ:
    TriCheck_dir = os.environ['TRICHECK_HOME']; 
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests/";
    herd_dir = os.environ['TRICHECK_HOME'] + "/util/herd/";
  else:
    TriCheck_dir = "";
    ctests_dir = "";
    herd_dir = "";

  # Parse command line opts/args
  try:
     opts, args = getopt.getopt(argv,"hT:c:H:",["help",
                                              "TriCheck=",
                                              "ctests=",
                                              "herd="]);
  except getopt.GetoptError:
     print usage_string;
     sys.exit(1);

  for opt, arg in opts:
     if opt in ('-h', "--help"):
       print usage_string;
       sys.exit();

     elif opt in ("-T", "--TriCheck"):
       TriCheck_dir = arg;

     elif opt in ("-c", "--ctests"):
       ctests_dir = arg;

     elif opt in ("-H", "--herd"):
       herd_dir = arg;

  if not os.path.isdir(os.path.expanduser(TriCheck_dir)):
    print "Have you set the $TRICHECK_HOME environment variable? \
           \nERROR: $TRICHECK_HOME directory does not exist...\n";
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(ctests_dir)):
    print "ERROR: C11 tests directory (ctests) is missing. Please specify or create one...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(herd_dir)):
    print "ERROR: Herd directory is missing. Please specify or create one...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isfile(herd_dir + "/c11_partialSC.cat"):
    print "ERROR: c11_partialSC.cat is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isfile(herd_dir + "/c11_base.cat"):
    print "ERROR: c11_base.cat is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isfile(herd_dir + "/sc.cat"):
    print "ERROR: sc.cat is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isfile(herd_dir + "/cpp_herd_to_pipecheck.py"):
    print "ERROR: cpp_herd_to_pipecheck.py is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  print "[TRICHECK...] Running helper/02-release-batch-cpp-herd-to-pipecheck.py to translate C11 litmus tests to ISA assembly equivalents...\n"

  print 'C11 tests directory is "' + ctests_dir + '"'
  print 'Herd directory is "' + herd_dir + '"'
  print 'TriCheck directory is "' + TriCheck_dir + '"\n'

  print "Generating assembly equivalents of C11 atomic tests...\n"

  genISATests(ctests_dir, TriCheck_dir, herd_dir)

  print ""

if __name__ == "__main__":
  main(sys.argv[1:])

