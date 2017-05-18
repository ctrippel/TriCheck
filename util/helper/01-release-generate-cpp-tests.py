#!/usr/bin/env python

from shutil import copyfile
import itertools
import fileinput
import fnmatch
import glob
import os
import re
import sys, getopt

read_orders = []
write_orders = []

def permuteTests(ctests_dir, templates_dir):
  templates = [];
  filename_bases = [];
  template_dict = {};
  num_read_types = 0;
  num_write_type = 0;

  # for each litmus test template, generate all permutations
  # of read_orders and write_orders
  print "Generating base tests... \n"

  # for each litmus test template in the templates directory
  for file in os.listdir(templates_dir):
    if not fnmatch.fnmatch(file, '*.litmus'):
      print "WARNING: Skipping invalid template file: " + ctests_dir + "/" + file;
      continue;
  
    filename_base = (re.search('(.+?).litmus', file)).group(1);

    # don't recreate test directories that already exit
    if os.path.isdir(ctests_dir + '/' + filename_base):
      print "WARNING: " + ctests_dir + "/" + filename_base + " exists already..."
      continue
  
    if fnmatch.fnmatch(file, '*.litmus'):
      templates.append(file);
      
    filename_bases.append(filename_base);

  # don't include duplicates  
  list(set(filename_bases));

  # now we have all filename bases, e.g., iriw for iriw.litmus
  for filename in filename_bases:

    # if this test directory doesn't exist, create it
    if not os.path.isdir(ctests_dir + '/' + filename):
      os.makedirs(ctests_dir + '/' + filename);
  
  for template in templates:
    filename_base = (re.search('(.+?).litmus', template)).group(1);
    template_dict[filename_base] = {}
    template_dict[filename_base]["reads"] = 0;
    template_dict[filename_base]["writes"] = 0;
 
    # determine the number of load and store placeholders 
    for line in fileinput.input(templates_dir + '/' + template):
      if re.match(".*<ORDER_LOAD>.*", line):
        template_dict[filename_base]["reads"] += 1;
      elif re.match(".*<ORDER_STORE>.*", line):
        template_dict[filename_base]["writes"] += 1;
  
  num_read_types =  len(read_orders);
  num_write_types = len(write_orders);
  
  for filename_base in template_dict:
      num_reads = template_dict[filename_base]["reads"]
      num_writes = template_dict[filename_base]["writes"]
  
      num_read_combinations  = (num_read_types ** num_reads  if (num_reads > 0)  else 0)
      num_write_combinations = (num_write_types ** num_writes if (num_writes > 0) else 0)
  
      read_combinations = [];
      write_combinations = [];
      
      # evaluate read permutations
      for i in range(0, num_read_combinations):
        read_set = [];
        for j in range(0, num_reads):
          read_set.append("");
        read_combinations.append(read_set);
  
      i = num_reads - 1
      while ( i >= 0 ):
        j = 0;
        while ( j < num_read_combinations ):
          for r_ord in read_orders:
            for k in range(0, (num_read_types ** i)):
              read_combinations[j+k][i] = r_ord;
            j += (num_read_types ** i);
        i -= 1;
  
      # evaluate write permutations
      for i in range(0, num_write_combinations):
        write_set = [];
        for j in range(0, num_writes):
          write_set.append("");
        write_combinations.append(write_set);
  
      i = num_writes - 1
      while ( i >= 0 ):
        j = 0;
        while ( j < num_write_combinations ):
          for w_ord in write_orders:
            for k in range(0, (num_write_types ** i)):
              write_combinations[j+k][i] = w_ord;
            j += (num_write_types ** i);
        i -= 1;
  
      num_read_combinations = len(read_combinations);
      num_write_combinations = len(write_combinations);
  
      read_index = -1;
      write_index = -1;
     
      # combine read and write permutations
      if (num_read_combinations > 0):
        read_index = 0;
        if (num_write_combinations > 0):
          write_index = 1;
          total_combinations = list(itertools.product(read_combinations, write_combinations))
        else:
            total_combinations = read_combinations;
  
      elif (num_write_combinations > 0):
        write_index = 0;
        total_combinations = write_combinations;
      else: 
        print "ERROR: check format of template " + filename_base;
        continue;
 
      # for each permuation, generated a unique .litmus file
      for i in range(0, len(total_combinations)):
        combination = list(total_combinations.pop(0))
        filename = filename_base
        #print combination
        reads = []; writes = [];
   
        if (read_index != -1):
          filename += "_R"
          for label in combination[read_index]:
            filename += "_" + label
          reads = combination[read_index]
        if (write_index != -1):
          filename += "_W"
          for label in combination[write_index]:
            filename += "_" + label
          writes = combination[write_index]
       
        r = 0; w = 0; f = 0;
        fp_out = open(ctests_dir + "/" + filename_base + "/" + filename + ".litmus", 'w');
  
        for line in fileinput.input(templates_dir + '/' + filename_base + '.litmus'):
          line = re.sub('<TEST>', filename, line);
          if (re.match('.*<ORDER_LOAD>.*', line)):
            line = re.sub('<ORDER_LOAD>', reads[r], line);
            r += 1
          if (re.match('.*<ORDER_STORE>.*', line)):
            line = re.sub('<ORDER_STORE>', writes[w], line);
            w += 1
          fp_out.write(line);
  
        fp_out.close();
          
# Main function
# Parse command line
# Call permuteTests
def main(argv):
  usage_string = "usage: \t 01-release-generate-cpp-tests.py [arguments] \
                  \n\nDescription: \tCreate C11 litmus tests using only atomic reads and writes. \
                                   \n\t\tAny ISA fence mappings will be generated later. \
                  \n\nArguments: \
                  \n\t-h or --help \t\t\t\t Display this help and exit \
                  \n\t-t or --templates <templates_dir> \t Assumed to be $TRICHECK_HOME/tests/templates \
                  \n\t-c or --ctests <ctests_dir> \t\t Assumed to be $TRICHECK_HOME/tests/ctests \
                  \n\t-x or --rlx \t\t\t\t Generate tests that use C11 \"relaxed\" read/write memory order primitives; default if nothing else specified \
                  \n\t-a or --acq \t\t\t\t Generate tests that use C11 \"acquire\" read memory order primitives \
                  \n\t-r or --rel \t\t\t\t Generate tests that use C11 \"release\" write memory order primitives \
                  \n\t-s or --sc \t\t\t\t Generate tests that use C11 \"seq_cst\" read/write memory order primitives \
                  \n\t-A or --all \t\t\t\t Generate tests that use all C11 read/write memory order primitives ";

  # Check if TRICHECK_HOME environment variable has been set
  if "TRICHECK_HOME" in os.environ:
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests";
    templates_dir = os.environ['TRICHECK_HOME'] + "/tests/templates/";
  else:
    ctests_dir = ""
    templates_dir = ""

  # Parse command line opts/args
  try:
     opts, args = getopt.getopt(argv,"ht:c:xarsfmA",["help",
                                                    "templates=",
                                                    "ctests=",
                                                    "rlx",
                                                    "acq",
                                                    "rel",
                                                    "sc",
                                                    "all"]);
  except getopt.GetoptError:
     print usage_string;
     sys.exit(1);

  for opt, arg in opts:
    if opt in ('-h', "--help"):
      print usage_string;
      sys.exit();

    elif opt in ("-t", "--templates"):
      templates_dir = arg

    elif opt in ("-c", "--ctests"):
      ctests_dir = arg

    elif opt in ("-x", "--rlx"):
      read_orders.append('relaxed');
      write_orders.append('relaxed');

    elif opt in ("-a", "--acq"):
      read_orders.append('acquire');

    elif opt in ("-r", "--rel"):
      write_orders.append('release');

    elif opt in ("-s", "--sc"):
      read_orders.append('seq_cst');
      write_orders.append('seq_cst');

    elif opt in ("-A", "--all"):
      read_orders.append('acquire');
      read_orders.append('seq_cst');
      write_orders.append('release');
      write_orders.append('seq_cst');
      read_orders.append('relaxed');
      write_orders.append('relaxed');

  # Check if the templates directory is a real directory
  if not os.path.isdir(templates_dir):
    print "ERROR: $TRICHECK_HOME/tests/templates directory is missing. Please specify or create one...\n"
    print usage_string;
    sys.exit(1);

  if os.listdir(templates_dir) == []:
    print "ERROR: No files in " + templates_dir + "\n"
    print usage_string;
    sys.exit(1);
   
  if not os.path.isdir(ctests_dir):
    os.makedirs(ctests_dir)

  print "[TRICHECK...] Running helper/01-release-generate-cpp-tests.py to generate C11 tests...\n"

  # tests don't make sense without reads and writes, so we
  # minimally generate tests with SC atomics and relaxed
  # reads and writes
  if (len(read_orders) == 0 and len(write_orders) == 0):
    print "No read or write memory orders were specified. Default is --rlx and --seq_cst."
    read_orders.append('relaxed');
    read_orders.append('seq_cst');
    write_orders.append('relaxed');
    write_orders.append('seq_cst');
  elif len(read_orders) == 0:
    print "No read memory orders were specified. Default is --rlx."
    read_orders.append('relaxed');
  elif len(write_orders) == 0:
    print "No write memory orders were specified. Default is --rlx."
    write_orders.append('relaxed');


  print 'C11 tests directory is "' + ctests_dir + '"'
  print 'Templates directory is "' + templates_dir + '"\n'

  permuteTests(ctests_dir, templates_dir)  

main(sys.argv[1:])

