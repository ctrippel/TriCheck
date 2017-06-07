#!/usr/bin/env python

from shutil import copyfile
import itertools
import fileinput
import fnmatch
import glob
import os
import re
import sys, getopt

def rmAtomicTests(ctests_dir):
  for file in glob.glob(ctests_dir + "/*/pipecheck/*"):
    if not fnmatch.fnmatch(file, '*fence*'):
      os.remove(file); 

def permuteTests(ctests_dir, templates_dir, mixedTests):
  templates = [];
  filename_bases = [];
  read_orders = {}
  write_orders = {}

  # for each litmus test template, generate all permutations
  print "Generating base tests..."

  # for each litmus test template in the templates directory
  for file in os.listdir(templates_dir):
    filename_base = (re.search('(.+?).litmus', file)).group(1);

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
  
  template_dict = {};
  
  for template in templates:
    filename_base = (re.search('(.+?).litmus', template)).group(1);
    template_dict[filename_base] = {}
    template_dict[filename_base]["reads"] = 0;
    template_dict[filename_base]["writes"] = 0;
 
    read_orders[filename_base] = []
    write_orders[filename_base] = []
 
    for line in fileinput.input(templates_dir + '/' + template):
      if re.match(".*<ORDER_LOAD>.*", line):
        template_dict[filename_base]["reads"] += 1;
      elif re.match(".*<ORDER_STORE>.*", line):
        template_dict[filename_base]["writes"] += 1;

    # only direct ISA mappings
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R*_relaxed*W?*.test") != []):
      read_orders[filename_base].append('relaxed_fence');
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R?*W*_relaxed*.test")!= []):
      write_orders[filename_base].append('relaxed_fence');
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*acquire*.test") != []):
      read_orders[filename_base].append('acquire_fence');
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*release*.test") != []):
      write_orders[filename_base].append('release_fence');
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R*_seq_cst*W?*.test") != []):
      read_orders[filename_base].append('seq_cst_fence');
    if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R?*W*_seq_cst*.test") != []):
      write_orders[filename_base].append('seq_cst_fence');

    # fence mappings 
    if(mixedTests):
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R*_relaxed*W?*.test") != []):
        read_orders[filename_base].append('relaxed');
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R?*W*_relaxed*.test")!= []):
        write_orders[filename_base].append('relaxed');
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*acquire*.test") != []):
        read_orders[filename_base].append('acquire');
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*release*.test") != []):
        write_orders[filename_base].append('release');
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R*_seq_cst*W?*.test") != []):
        read_orders[filename_base].append('seq_cst');
      if (glob.glob(ctests_dir + "/" + filename_base + "/pipecheck/*R?*W*_seq_cst*.test") != []):
        write_orders[filename_base].append('seq_cst');

   
  for filename_base in template_dict:
      num_read_types = len(read_orders[filename_base])
      num_write_types = len(write_orders[filename_base])

      num_reads = template_dict[filename_base]["reads"]
      num_writes = template_dict[filename_base]["writes"]
  
      num_read_combinations  = (num_read_types ** num_reads  if (num_reads > 0)  else 0)
      num_write_combinations = (num_write_types ** num_writes if (num_writes > 0) else 0)
  
      read_combinations = [];
      write_combinations = [];
      
      for i in range(0, num_read_combinations):
        read_set = [];
        for j in range(0, num_reads):
          read_set.append("");
        read_combinations.append(read_set);
  
      i = num_reads - 1
      while ( i >= 0 ):
        j = 0;
        while ( j < num_read_combinations ):
          for r_ord in read_orders[filename_base]:
            for k in range(0, (num_read_types ** i)):
              read_combinations[j+k][i] = r_ord;
            j += (num_read_types ** i);
        i -= 1;
  
  
      for i in range(0, num_write_combinations):
        write_set = [];
        for j in range(0, num_writes):
          write_set.append("");
        write_combinations.append(write_set);
  
      i = num_writes - 1
      while ( i >= 0 ):
        j = 0;
        while ( j < num_write_combinations ):
          for w_ord in write_orders[filename_base]:
            for k in range(0, (num_write_types ** i)):
              write_combinations[j+k][i] = w_ord;
            j += (num_write_types ** i);
        i -= 1;
  
      num_read_combinations = len(read_combinations);
      num_write_combinations = len(write_combinations);
  
      read_index = -1;
      write_index = -1;
     
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
  
      for i in range(0, len(total_combinations)):
        combination = list(total_combinations.pop(0))
        filename = filename_base
        
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
        fn_out = ctests_dir + "/" + filename_base + "/pipecheck/" + filename + ".test";
        if os.path.exists(fn_out):
          continue;
        fp_out = open(fn_out, 'w');
        
        fn_in = fn_out.replace('_fence', '');
        for line in fileinput.input(fn_in):
          line = re.sub('<TEST>', filename, line);
          if (re.match('.*Read.*', line)):
            if reads[r] not in ['relaxed', 'acquire','seq_cst']:
              line = re.sub('Read', 'Read ' + reads[r] + ' ', line);
            r += 1
          if (re.match('.*Write.*', line)):
            if writes[w] not in ['relaxed', 'release','seq_cst']:
              line = re.sub('Write', 'Write ' + writes[w] + ' ', line);
            w += 1
          fp_out.write(line);
  
        fp_out.close();
          
  
def main(argv):
  mixedTests = False;
  fenceTests = False;


  usage_string = "usage: \t 03-preprocess.py [arguments] \
                 \n\nDescription: \tCreate intermediate represenation litmus tests that annotate operations that use fence mappings. \
                 \n\nArguments: \
                 \n\t-t or --templates <templates_dir> \t Assumed to be $TRICHECK_HOME/tests/templates \
                 \n\t-o or --tests <tests_dir> \t\t Assumed to be $TRICHECK_HOME/tests \
                 \n\t-a or --atomics \t\t\t Generate tests that use ISA quivalents of C11 atomic primitives \
                 \n\t-f or --fences \t\t\t\t Generate tests that use fence mappings in compile.txt \
                 \n\t-m or --mixed \t\t\t\t Generate tests that use a combination of atomics and fence mappings in compile.txt";


  atomicTests = False;
  fenceTests = False;
  mixedTests = False;

  if "TRICHECK_HOME" in os.environ:
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests";
    templates_dir = os.environ['TRICHECK_HOME'] + "/tests/templates/";
  else:
    ctests_dir = ""
    templates_dir = ""

  try:
     opts, args = getopt.getopt(argv,"ht:c:Cfm",["help",
                                                 "templates=",
                                                 "ctests=",
                                                 "atomics",
                                                 "fences",
                                                 "mixed"]);
  except getopt.GetoptError:
     print usage_string;
     sys.exit(1)

  for opt, arg in opts:
    if opt in ('-h', "--help"):
      print usage_string;
      sys.exit()

    elif opt in ("-t", "--templates"):
      templates_dir = arg

    elif opt in ("-c", "--ctests"):
      ctests_dir = arg

    elif opt in ("-C", "--atomics"):
      atomicTests = True;

    elif opt in ("-m", "--mixed"):
      mixedTests = True;

    elif opt in ("-f", "--fences"):
      fenceTests = True;


  if not os.path.isdir(os.path.expanduser(templates_dir)):
    print "ERROR: $TRICHECK_HOME/tests/templates directory is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  if not os.path.isdir(os.path.expanduser(ctests_dir)):
    print "ERROR: C11 tests directory (ctests) is missing. Please specify or create one..."
    print usage_string;
    sys.exit(1)

  print "[TRICHECK...] Running helper/03-preprocss.py to mark operations that use fence mappings...\n"

  # default is fence tests
  if (~atomicTests and ~mixedTests and ~fenceTests):
    print "Prference of atomics vs. fences was not specified. Default is --fences."
    fenceTests = True;

  print 'C11 tests directory is "' + ctests_dir + '"'
  print 'Templates directory is "' + templates_dir + '"\n'

  if (fenceTests or mixedTests):
    permuteTests(ctests_dir, templates_dir, mixedTests)  

  if not atomicTests:
    rmAtomicTests(ctests_dir)

  print ""

main(sys.argv[1:])

