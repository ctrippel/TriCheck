# TriCheck

TriCheck is a methodology and automated tool for verifying that a particular
combination of high-level language (HLL), compiler mappings from said HLL to
an ISA target, and microarchitectural implementation of said ISA, collectively
preserve memory consistency model requirements.

TriCheck is derived from PipeCheck, CCICheck, and COATCheck.  Much of the
terminology and naming comes from those tools. See those papers/websites
for details.

http://github.com/daniellustig/pipecheck

http://github.com/ymanerka/ccicheck

http://github.com/daniellustig/coatcheck

### Citing TriCheck

If you use our tool in your work, we would appreciate it if you cite our paper(s):

Daniel Lustig, Michael Pellauer, and Margaret Martonosi.  "PipeCheck:
  Specifying and Verifying Microarchitectural Enforcement of Memory Consistency
  Models", *47th International Symposium on Microarchitecture (MICRO)*,
  Cambridge UK, December 2014.

Yatin Manerkar, Daniel Lustig, Michael Pellauer, and Margaret Martonsi.
  "CCICheck: Using uhb Graphs to Verify the Coherence-Consistency Interface",
  *48th International Symposium on Microarchitecture (MICRO)*,
  Honolulu, HI, December 2015.

Daniel Lustig+, Geet Sethi+, Margaret Martonosi, and Abhishek Bhattacharjee.
  "COATCheck: Verifying Memory Ordering at the Hardware-OS Interface",
  *21st International Conference on Architectural Support for Programming
  Languages and Operating Systems (ASPLOS)*, Atlanta, GA, April 2016.
  (+: joint first authors)

Caroline Trippel, Yatin Manerkar, Daniel Lustig, Michael Pellauer, and Margaret Martonosi. 
  "TriCheck: Memory Model Verification at the Trisection of Software, Hardware, and ISA", 
  *22nd International Conference on Architectural Support for Programming Languages and
  Operating Systems (ASPLOS)*, Xi'an, China.\, April 2017.

### Contacting the authors

If you have any comments, questions, or feedback, please contact Caroline Trippel
at ctrippel@princeton.edu, or visit our GitHub page, github.com/ctrippel/TriCheck.

### Status

At this point, TriCheck is a research tool rather than an industry-strength
verification toolchain.  We do appreciate any suggestions or feedback either
in approach or in implementation.  If you are interested in any particular
feature, missing item, or implementation detail, please contact the authors and
we will try to help out as best we can.

## Building and Using TriCheck

### Prerequisites

TriCheck leverages the COATCheck which is derived from PipeCheck and CCICheck.
COATCheck must be build prior to running TriCheck. See the build instructions at:

http://github.com/daniellustig/coatcheck

TriCheck also leverages Herd devloped by Jade Alglave and Luc Maranget. See build
instructions at:

https://github.com/herd/herdtools

The remainder of TriCheck requires Python and has been tested with Python v2.7.5.
