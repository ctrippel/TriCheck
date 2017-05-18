#!/usr/bin/env python

import fileinput
import sys
import os
import fnmatch
import subprocess
import tempfile
import re
import json
import gzip
import sys, getopt

fenceMappingsPrefix = { "Read relaxed_fence" : [],
                        "Write relaxed_fence" : [], 
                        "Read acquire_fence" : [], 
                        "Write release_fence" : [], 
                        "Read seq_cst_fence" : [], 
                        "Write seq_cst_fence" : []} 

fenceMappingsSuffix = { "Read relaxed_fence" : [],
                        "Write relaxed_fence" : [], 
                        "Read acquire_fence" : [], 
                        "Write release_fence" : [], 
                        "Read seq_cst_fence" : [], 
                        "Write seq_cst_fence" : []} 

newIndDir = {}

def parseFenceMappings():
  fenceMappings = os.environ['TRICHECK_HOME'] + "/util/compile.txt";
  if not os.path.exists(fenceMappings):
    print "ERROR: Missing file " + fenceMappings + "..."
    sys.exit(1);

  for line in fileinput.input(fenceMappings):
    if (re.match("^(Read|Write)", line)):
      line_array = line.split('|');
      c_op = line_array[0].strip() + "_fence";
      prefix = (line_array[1].strip()).split(';');
      suffix = (line_array[2].strip()).split(';');
      
      for pre in prefix:
        if pre == "NA":
          continue;
        fenceMappingsPrefix[c_op].append(pre);
      for suff in suffix:
        if suff == "NA":
          continue;
        fenceMappingsSuffix[c_op].append(suff);

def getNewInd(ctests_dir):
  for dir in os.listdir(ctests_dir):
    for test in os.listdir(ctests_dir + '/' + dir + '/pipecheck'):
      if fnmatch.fnmatch(test, '*.test'):
        for line in fileinput.input(ctests_dir + '/' + dir + '/pipecheck/' + test):
          match_inst = re.match('^([0-9]+).*', line);
          if (match_inst):
            inst_max = int(match_inst.group(1));
          if (re.match('^Relationship.*', line)):
            newIndDir[dir] = inst_max;
            fileinput.close();
            break;
      break;

def applyFenceMappings(ctests_dir):
  # expand fence
  print "Creating fence variants..."
  for dir in os.listdir(ctests_dir):
    for file in os.listdir(ctests_dir + '/' + dir + '/pipecheck' ):
      if fnmatch.fnmatch(file, dir + '*fence*.test'):

        relationship_str = ""
        new_ind = newIndDir[dir] + 1;
        prev_inst = []
        post_inst = []
        po_prev = {}
        po_post = {}

        filename = ctests_dir + '/' + dir + '/pipecheck/mapped+' + file;
        file_out = open(filename, "w");
        
        for line in fileinput.input(ctests_dir + '/' + dir + '/pipecheck/' + file):
          if (re.match('^(Permitted|Forbidden)', line)):
            # enumeration of po ending in new fences
            for core in po_prev:
              for inst in po_prev[core]:
                if int(inst) >= newIndDir[dir] + 1:
                  for prev in (po_prev[core])[inst]:
                    relationship_str += "Relationship po " + prev + " 0 -> " + inst + " 0\n"
          
            # enumeration of po ending starting with new fences
            for core in po_post:
              for inst in po_post[core]:
                if int(inst) >= newIndDir[dir] + 1:
                  for post in (po_post[core])[inst]:
                    relationship_str += "Relationship po " + inst + " 0 -> " + post + " 0\n"
            line = relationship_str + line;
          else:
            match_inst = re.match('^([0-9]+)(\s+)([0-9]+)(\s+)([0-9]+)(\s+)([0-9]+)(\s+).*', line);
            if (match_inst):
              inst_ind = match_inst.group(1);
              core_ind = match_inst.group(3);
              xtra1_ind = match_inst.group(5);
              xtra2_ind = match_inst.group(7);

              if core_ind not in po_prev:
                po_prev[core_ind] = {}
                po_post[core_ind] = {}
                prev_inst = []

              prefix = ""
              suffix = ""

              # Read relaxed fence mapping
              match = re.match('.*(Read|Write)(\s+)(.*_fence)(\s+)(Rlx|Acq|Rel|Sc).*', line);
              if (match):
                mem_type =  match.group(1);
                fence_type = match.group(3);
                atomic_type = match.group(5);

                line = re.sub(mem_type + "(\s+)" + fence_type + "(\s+)" + atomic_type, mem_type + " Rlx", line);
                for pre in fenceMappingsPrefix[mem_type + " " + fence_type]:
                  prefix += str(new_ind) + " " + core_ind + " " + xtra1_ind + " " + xtra2_ind +  " (Fence " + pre + " )\n"

                  (po_prev[core_ind])[str(new_ind)] = [];
                  (po_prev[core_ind])[str(new_ind)].extend(prev_inst); 
                  prev_inst.append(str(new_ind));

                  for inst in (po_post[core_ind]):
                    (po_post[core_ind])[inst].append(str(new_ind));
                  (po_post[core_ind])[str(new_ind)] = [];          

                  new_ind += 1;
                  

                (po_prev[core_ind])[inst_ind] = [];
                (po_prev[core_ind])[inst_ind].extend(prev_inst); 
                prev_inst.append(inst_ind);

                for inst in (po_post[core_ind]):
                  (po_post[core_ind])[inst].append(inst_ind);
                (po_post[core_ind])[inst_ind] = [];          
                  
                for suff in fenceMappingsSuffix[mem_type + " " + fence_type]:
                  suffix += str(new_ind) + " " + core_ind + " " + xtra1_ind + " " + xtra2_ind +  "(Fence " + suff + " )\n"

                  (po_prev[core_ind])[str(new_ind)] = [];
                  (po_prev[core_ind])[str(new_ind)].extend(prev_inst); 
                  prev_inst.append(str(new_ind));

                  for inst in (po_post[core_ind]):
                    (po_post[core_ind])[inst].append(str(new_ind));
                  (po_post[core_ind])[str(new_ind)] = [];          

                  new_ind += 1;

              else:
                (po_prev[core_ind])[inst_ind] = [];
                (po_prev[core_ind])[inst_ind].extend(prev_inst); 
                prev_inst.append(inst_ind);
   
                for inst in (po_post[core_ind]):
                  (po_post[core_ind])[inst].append(inst_ind);
                (po_post[core_ind])[inst_ind] = [];          
                
  
              line = prefix + line + suffix;
  
          file_out.write(line);
        file_out.close();
        os.rename(ctests_dir + '/' + dir + '/pipecheck/mapped+' + file, ctests_dir + '/' + dir + '/pipecheck/' + file);

def main(argv):
  mixedTests = False;
  fenceTests = False;

  usage_string = "usage: \t 04-postprocess.py [arguments] \
                  \n\nDescription: \tIf --fence or --mixed flags are specified, parse compile.txt to determine user-specified fence mappings for C11 atomics.\
                                   \n\t\tExpand ISA fence mappings for all litmus tests that use fences. \
                  \n\nArguments: \
                  \n\t-h or --help \t\t\t\t Display this help and exit \
                  \n\t-c or --ctests <ctests_dir> \t\t Assumed to be $TRICHECK_HOME/tests/ctests";

  if "TRICHECK_HOME" in os.environ:
    ctests_dir = os.environ['TRICHECK_HOME'] + "/tests/ctests/";

  else:
    ctests_dir = "";

  try:
     opts, args = getopt.getopt(argv,"hc:",["ctests=", "help"])

  except getopt.GetoptError:
     print usage_string
     sys.exit(1)
  for opt, arg in opts:
     if opt in ("-h", "--help"):
       print usage_string
       sys.exit()

     elif opt in ("-c", "--ctests"):
       templates_dir = arg

  if not os.path.isdir(ctests_dir):
    print "ERROR: C11 tests directory (ctests) is missing. Please specify or create one...\n"
    print usage_string;
    sys.exit(1)

  print "[TRICHECK...] Running helper/04-postprocess.py to expand ISA fence mappings for tests that use fences...\n"

  print 'C11 tests directory is "' + ctests_dir + '"\n'

  parseFenceMappings();
  getNewInd(ctests_dir);
  applyFenceMappings(ctests_dir)

  print ""

main(sys.argv[1:])

