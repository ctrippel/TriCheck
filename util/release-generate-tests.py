#!/usr/bin/env python

from shutil import copyfile
import itertools
import fileinput
import fnmatch
import glob
import os
import re
import sys, getopt

def main(argv):
  mixedTests = False;

  # Opts to pass to helper scripts
  py_01_opts = ""
  py_02_opts = ""
  py_03_opts = ""
  py_04_opts = ""


  usage_string = "usage: \t release-generate-tests.py [arguments] \
                 \n\nDescription: \tCreate C11 litmus tests and corresponding ISA litmus tests. \
                 \n\nArguments: \
                 \n\t-h or --help \t\t\t\t Display this help and exit \
                 \n\t-T or --TriCheck <TriCheck_dir> \t Assumed to be $TRICHECK_HOME \
                 \n\t-t or --templates <templates_dir> \t Assumed to be $TRICHECK_HOME/tests/templates \
                 \n\t-c or --ctests <ctests_dir> \t\t Assumed to be $TRICHECK_HOME/tests/ctests \
                 \n\t-H or --herd <herd_dir> \t\t Assumed to be $TRICHECK_HOME/herd \
                 \n\t-x or --rlx \t\t\t\t Generate tests that use C11 \"relaxed\" read/write memory order primitives; default if nothing else specified \
                 \n\t-a or --acq \t\t\t\t Generate tests that use C11 \"acquire\" read memory order primitives \
                 \n\t-r or --rel \t\t\t\t Generate tests that use C11 \"release\" write memory order primitives \
                 \n\t-s or --sc \t\t\t\t Generate tests that use C11 \"seq_cst\" read/write memory order primitives \
                 \n\t-A or --all \t\t\t\t Generate tests that use all C11 read/write memory order primitives\
                 \n\t-C or --atomics \t\t\t Generate tests that use ISA atomics \
                 \n\t-f or --fences \t\t\t\t Generate tests that use fence mappings in compile.txt \
                 \n\t-m or --mixed \t\t\t\t Generate tests that use a combination of atomics and fence mappings in compile.txt";

  # Check if TRICHECK_HOME exists
  if "TRICHECK_HOME" in os.environ:
    TriCheck_dir = os.environ['TRICHECK_HOME'];
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests";
    herd_dir = os.environ['TRICHECK_HOME'] + "/util/herd";
    templates_dir = os.environ['TRICHECK_HOME'] + "/tests/templates/";
  else:
    TriCheck_dir = ""
    ctests_dir = ""
    herd_dir = ""
    templates_dir = ""

  # Try to parse opts
  try:
    opts, args = getopt.getopt(argv,"hT:t:c:H:xarsACfm",["help",
                                                     "TriCheck=",
                                                     "templates=",
                                                     "ctests=",
                                                     "herd=",
                                                     "rlx",
                                                     "acq",
                                                     "rel",
                                                     "sc",
                                                     "all",
                                                     "atomics",
                                                     "fences",
                                                     "mixed"]);

  except getopt.GetoptError:
     print usage_string;
     sys.exit(1)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print usage_string;
      sys.exit()

    elif opt in ("-T", "--TriCheck"):
      TriCheck_dir = arg
      py_02_opts += " --TriCheck=" + arg

    elif opt in ("-t", "--templates"):
      templates_dir = arg
      py_01_opts += " --templates=" + arg
      py_03_opts += " --templates=" + arg

    elif opt in ("-H", "--herd"):
      herd_dir = arg
      py_02_opts += " --herd=" + arg

    elif opt in ("-c", "--ctests"):
      ctests_dir = arg
      py_01_opts += " --ctests=" + arg
      py_02_opts += " --ctests=" + arg
      py_03_opts += " --ctests=" + arg
      py_04_opts += " --ctests=" + arg

    elif opt in ("-x", "--rlx"):
      py_01_opts += " --rlx";

    elif opt in ("-a", "--acq"):
      py_01_opts += " --acq";

    elif opt in ("-r", "--rel"):
      py_01_opts += " --rel";

    elif opt in ("-s", "--sc"):
      py_01_opts += " --sc";

    elif opt in ("-C", "--atomics"):
      py_03_opts += " --atomics"

    elif opt in ("-f", "--fences"):
      py_03_opts += " --fences"

    elif opt in ("-m", "--mixed"):
      py_03_opts += " --mixed"

    elif opt in ("-A", "--all"):
      py_01_opts += " --all";

  if not os.path.isdir(os.path.expanduser(TriCheck_dir)):
    print "$TRICHECK_HOME directory is missing. Please create one..."
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(templates_dir)):
    print "$TRICHECK_HOME/tests/templates directory is missing. Please create one..."
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

  if not os.path.isfile(herd_dir + "/sc.cat"):
    print "ERROR: sc.cat is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isfile(herd_dir + "/cpp_herd_to_pipecheck.py"):
    print "ERROR: c11_partialSC.cat is missing from herd directory...\n"
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(ctests_dir)):
    os.makedirs(ctests_dir)

  helper01 = TriCheck_dir + "/util/helper/01-release-generate-cpp-tests.py " + py_01_opts;
  helper02 = TriCheck_dir + "/util/helper/02-release-batch-cpp-to-pipecheck.py " + py_02_opts;
  helper03 = TriCheck_dir + "/util/helper/03-preprocess.py " + py_03_opts;
  print "helper03: ", helper03
  helper04 = TriCheck_dir + "/util/helper/04-postprocess.py " + py_04_opts;

  helper_scripts = [helper01, helper02, helper03, helper04]
  for helper in helper_scripts:
    try:
      os.system(helper);
    except:
      print "ERROR: Missing helper file? Errors occured in running: " + helper
      print usage_string;
      sys.exit(1)

main(sys.argv[1:])

