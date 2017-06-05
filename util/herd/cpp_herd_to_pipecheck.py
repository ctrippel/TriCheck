#!/usr/bin/env python

import sys
import os
import subprocess
import tempfile
import re
import json
import gzip

rw_re = '([RW])(\(.+?\))?([^\*]+)(\*?)=(.+?)'
#rw_re = '([RW])\((.+?)\)([^\*]+)(\*?)=(.+?)'
#rw_re2 = '([RW])([^\*]+)(\*?)=(.+?)'
node_re = 'eiid([0-9]+) \[label="[a-z0-9]+: (.*)\\\\lproc:([0-9]+) poi:([0-9])'
final_node_re = '^finaleiid([0-9]+)'
edge_re = '^eiid([0-9]+) -> eiid([0-9]+) .*label="([^"]*)"'
#init_re = 'initeiid([0-9]+)'
#init_re = '^eiid([0-9]+).*\\\\lInit.*'
final_re = '([^ (]+) *= *([^ \\\/\)$]*)'
init_re = '^eiid([0-9]+).*[WR](.).*\\\\lInit.*'

#Mappings = {"IBM370"	: 	{
#				 "Read"	:	{"Rlx": "", "Acq": "", "Sc": ""},
#				 "Write":	{"Rlx": "", "Rel": "", "Sc": ""},
#				 "Fence":	{"Acq": "", "Rel": "", "Sc": ""}
#				}
#	    "IBM370"    :       {
#                                 "Read" :       {"Rlx": "", "Acq": "", "Sc": ""},
#                                 "Write":       {"Rlx": "", "Rel": "", "Sc": ""},
#                                 "Fence":       {"Acq": "", "Rel": "", "Sc": ""}
#                                }
#	    "IBM370"    :       {
#                                 "Read" :       {"Rlx": "", "Acq": "", "Sc": ""},
#                                 "Write":       {"Rlx": "", "Rel": "", "Sc": ""},
#                                 "Fence":       {"Acq": "", "Rel": "", "Sc": ""}
#                                }
#	    "IBM370"    :       {
#                                 "Read" :       {"Rlx": "", "Acq": "", "Sc": ""},
#                                 "Write":       {"Rlx": "", "Rel": "", "Sc": ""},
#                                 "Fence":       {"Acq": "", "Rel": "", "Sc": ""}
#                                }
#            "TSO"	: 	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "PSO"	: 	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "PC"	: 	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "RMO"	: 	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "ARM"	:	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "IBM370+A"	:  	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "TSO+A"	:  	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "PSO+A"	:  	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "PC+A"	:  	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "RMO+A"	:  	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""},
#            "ARM+A" 	: 	{"Rlx": "", "Acq": "", "Rel": "", "AR": "", "Sc": ""}};

def Dirn(d, t):
    op = ""
    if d == "R":
        op =  "Read"
    elif d == "W":
        op = "Write"
    else:
        raise Exception("Unknown dirn")

    if t == "(Rlx)":
        return op + " Rlx"
    elif t == "(Acq)":
        return op + " Acq"
    elif t == "(Rel)":
        return op + " Rel"
    elif t == "(AR)":
        return op + " AR"
    elif t == "(Sc)":
        return op + " Sc"
    elif t == None:
        return op
    else:
        raise Exception("Unknown dirn type")

def Addr(v):
    try:
        return Addr.addrs.setdefault(v, int(v))
    except ValueError:
        return Addr.addrs.setdefault(v, max(Addr.addrs.values()) + 1)
Addr.addrs = {"x": 0, "y": 1, "z": 2, "w": 3}

def Data(v):
    try:
        return Data.datas.setdefault(v, int(v))
    except ValueError:
        return Data.datas.setdefault(v, max(Data.datas.values()) + 1)
Data.datas = {"0": 0}

class PTE:
    def __init__(self, a, c, d):
        self.a = a
        self.c = c
        self.d = d
    def __str__(self):
        return "(PTE VTAG %d -> PTAG %d %sacc %sdirty)" % (
                self.a, self.a, "" if self.c else "!",
                "" if self.d else "!")

class Node:
    def __str__(self):
        s = "%d %d 0 %d (%s %s" % (self.eiid, self.proc, self.iiid, self.action, self.atype)
        if self.action in ["Read",  "Read Rlx",   "Read Acq",  "Read Rel",  "Read AR",  "Read Sc",
                           "Write", "Write Rlx",  "Write Acq", "Write Rel", "Write AR", "Write Sc"]:
            for d in self.data:
                data = d
                break
            if type(data) == int:
                data = "(Data %d)" % data

            s += " (VA %d 0) (PA %d 0) %s" % (
                    self.addr, self.addr,
                    data if len(self.data) == 1 else "?")
        s += ")\n"
        return s
    def __eq__(self, other):
        if not (self.eiid == other.eiid and self.proc == other.proc and
                self.iiid == other.iiid and
                self.action == other.action and self.atype == other.atype):
            return False
        if self.action in ["Read",  "Read Rlx",   "Read Acq",  "Read Rel",  "Read AR",  "Read Sc",
                           "Write", "Write Rlx",  "Write Acq", "Write Rel", "Write AR", "Write Sc"]:
            if self.addr != other.addr:
                return False
            for d in self.data:
                if d not in other.data:
                    return False
            for d in other.data:
                if d not in self.data:
                    return False
        return True
    def sameModData(self, other):
        if self.action in ["Read",  "Read Rlx",  "Read Acq",  "Read Rel",  "Read AR",  "Read Sc",
                           "Write", "Write Rlx",  "Write Acq", "Write Rel", "Write AR", "Write Sc"]:
            return (self.eiid == other.eiid and self.proc == other.proc and
                    self.action == other.action and
                    self.atype == other.atype and self.addr == other.addr)
        else:
            return (self.eiid == other.eiid and self.proc == other.proc and
                    self.action == other.action and
                    self.atype == other.atype)
    def dupWithData(self, d):
        n = Node()
        n.iiid = self.iiid
        n.eiid = self.eiid
        n.proc = self.proc
        n.action = self.action
        n.atype = self.atype

        try:
            n.addr = self.addr
            assert d
            n.data = set(d)
        except AttributeError:
            pass
        return n
    def Action(self, a):
        match = re.search(rw_re, a)
        if match:
            #print match.group(1), match.group(2), match.group(3), match.group(4), match.group(5) 
            self.action = Dirn(match.group(1), match.group(2))
            self.addr   = Addr(match.group(3))
            self.atype  = "RMW" if match.group(4) == '*' else ""
            self.data   = set([Data(match.group(5))])
        else:
            self.action = "Fence"
            match = re.search("\((.+?)\)", a)
            #self.atype  = a
            self.atype  = match.group(1)

class Edge:
    def __init__(self, src=None, dst=None, lbl=None):
        self.src = src
        self.dst = dst
        self.lbl = lbl
    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst and \
                self.lbl == other.lbl
    def __str__(self):
        return "Relationship %s %d 0 -> %d 0\n" % (
                self.lbl, self.src, self.dst)

class Condition:
    def __str__(self):
        return "(PA %d 0) = %d\n" % (self.addr, self.data)

#def EnumerateNodeValues(l):
#    buf_in = [[]]
#    buf_out = []
#    for n in l:
#        #sys.stderr.write("ENV: n=%s" % str(n))
#        try:
#            for d in n.data:
#                #sys.stderr.write("ENV: d=%d\n" % d)
#                for i in buf_in:
#                    buf_out.append(i + [n.dupWithData([d])])
#        except AttributeError:
#            for i in buf_in:
#                buf_out.append(i + [n.dupWithData(None)])
#        #sys.stderr.write("ENV: in=%d out=%d\n" % (len(buf_in), len(buf_out)))
#        buf_in = buf_out
#        buf_out = []
#    return buf_in
#
#def MergeNodes(a, b):
#    if not a.sameModData(b):
#        sys.stderr.write("Address changed between nodes?\n")
#        return None
#    try:
#        return a.dupWithData(a.data | b.data)
#    except AttributeError:
#        return a.dupWithData(None)
#
def TryMerge(a, b, finals):
    r = {}
    #sys.stderr.write("TryMerge: input\n")
    #for (eiid, n) in parse_graph.nodes[a].iteritems():
    #    sys.stderr.write(str(n))
    for i in parse_graph.nodes[a].iteritems():
        if i not in parse_graph.nodes[b].items():
            #sys.stderr.write("TM: can't merge: %s\n" % str(i))
            return False
    for i in parse_graph.nodes[b].iteritems():
        if i not in parse_graph.nodes[a].items():
            #sys.stderr.write("TM: can't merge: %s\n" % str(i))
            return False
    #sys.stderr.write("TryMerge: output\n")
    # re = EnumerateNodeValues(r.values())
    # ae = EnumerateNodeValues(parse_graph.nodes[a].values())
    # be = EnumerateNodeValues(parse_graph.nodes[b].values())
    # for i in re:
    #     if i not in ae and i not in be:
    #         #sys.stderr.write("TM: can't merge:\n")
    #         #for n in i:
    #         #    sys.stderr.write(str(n))
    #         return False
    for e in parse_graph.edges[a]:
        if e not in parse_graph.edges[b]:
            if sys.argv[5] == "all":
                #sys.stderr.write("TM: can't merge: %s" % str(e))
                return False
            elif sys.argv[5] == "po":
                if e.lbl == "po":
                    #sys.stderr.write("TM: can't merge: %s" % str(e))
                    return False
            elif sys.argv[5] == "power":
                if e.lbl in ["po", "addr", "ctrl", "data"]:
                    #sys.stderr.write("TM: can't merge: %s" % str(e))
                    return False
                elif e.lbl in ["rf", "co", "fr", "ppo", "GHB", "prop", "propbase", "scp"]:
                    pass
                else:
                    raise Exception("Unknown edge %s" % e.lbl)
            else:
                assert False
    for e in parse_graph.edges[b]:
        if e not in parse_graph.edges[a]:
            if sys.argv[5] == "all":
                #sys.stderr.write("TM: can't merge: %s" % str(e))
                return False
            elif sys.argv[5] == "po":
                if e.lbl == "po":
                    #sys.stderr.write("TM: can't merge: %s" % str(e))
                    return False
            elif sys.argv[5] == "power":
                if e.lbl in ["po", "addr", "ctrl", "data"]:
                    #sys.stderr.write("TM: can't merge: %s" % str(e))
                    return False
                elif e.lbl in ["rf", "co", "fr", "ppo", "GHB", "prop", "propbase", "scp"]:
                    pass
                else:
                    raise Exception("Unknown edge %s" % e.lbl)
            else:
                assert False

    for f in parse_graph.finals[a]:
        if f not in parse_graph.finals[b]:
            n = parse_graph.nodes[a][f]
            if n.addr in finals:
                return False

    for f in parse_graph.finals[b]:
        if f not in parse_graph.finals[a]:
            n = parse_graph.nodes[b][f]
            if n.addr in finals:
                return False

    return True

def TransitiveClosure(edges, label):
    nodes = set()
    for e in edges:
        if e.lbl == label:
            nodes.add(e.src)
            nodes.add(e.dst)
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if Edge(i, k, label) in edges and \
                        Edge(k, j, label) in edges and \
                        Edge(i, j, label) not in edges:
                    edges.append(Edge(i, j, label))
    return edges

def OnlyMemberOf(s):
    assert len(s) == 1
    for x in s:
        return x

def parse_graph(contents, f, finals, outcome):
    parse_graph.nodes = []
    parse_graph.edges = []
    parse_graph.inits = {}
    parse_graph.finals = []

    inits = []


    for ln in f:
        match = "digraph" in ln
        if match:
            parse_graph.nodes.append({})
            parse_graph.edges.append([])
            parse_graph.finals.append(set())
        match = re.search(init_re,ln)
        if match:
            inits.append(int(match.group(1)))
        match = re.search(node_re, ln)
        if match:
            node = Node()
            node.iiid =  0
            node.eiid =  int(match.group(1))
            node.Action     (match.group(2))
            node.proc =  int(match.group(3))
            node.poi  =  int(match.group(4))
            parse_graph.nodes[-1][node.eiid] = node
        match = re.search(final_node_re, ln)
        if match:
            eiid = int(match.group(1))
            parse_graph.finals[-1].add(eiid)
        match = re.search(edge_re, ln)
        if match:
            if not int(match.group(1)) in inits:
                edge = Edge()
                edge.src = int(match.group(1))
                edge.dst = int(match.group(2))
                edge.lbl =     match.group(3)
                parse_graph.edges[-1].append(edge)
            elif int(match.group(1)) in inits:
                init = Condition()
                init.eiid = int(match.group(2))
                init.addr = parse_graph.nodes[-1][init.eiid].addr
                assert len(parse_graph.nodes[-1][init.eiid].data) == 1
                init.data = OnlyMemberOf(parse_graph.nodes[-1][init.eiid].data)
                
                if init.data != 0:
                    if init.addr not in parse_graph.inits.keys():
                        #MIGHT NOT NEED THIS ASSERT
			#assert parse_graph.inits[init.addr].data == init.data
                    #else:
                        parse_graph.inits[init.addr] = init

    #f.seek(0, 0)
    #for ln in f:
    #    match = re.search(edge_re, ln)
    #    if match:

    for i in parse_graph.inits.itervalues():
        # CJT COMMENT contents["pipechecktest"] += str(i)
        contents["pipechecktest"] += "" #str(i)

    # Workarounds for herd's quirks
    for n in range(len(parse_graph.edges)):
        edges = []
        for e in parse_graph.edges[n]:
            if parse_graph.nodes[n][e.dst].action == "Fence" and \
                    e.lbl == "ctrl":
                e2 = Edge()
                e2.src = e.src
                e2.dst = e.dst
                e2.lbl = "po"
                edges.append(e2)
            if parse_graph.nodes[n][e.src].atype != "Commit" and \
                    parse_graph.nodes[n][e.dst].atype != "Commit":
                edges.append(e)
        parse_graph.edges[n] = edges



    for n in range(len(parse_graph.nodes)):
        nodes = {}
        for (eiid, node) in parse_graph.nodes[n].iteritems():
            if node.atype != "Commit":
                nodes[eiid] = node
        parse_graph.nodes[n] = nodes

    for n in range(len(parse_graph.edges)):
        parse_graph.edges[n] = TransitiveClosure(parse_graph.edges[n], "po")

    repeat = True
    pre = len(parse_graph.nodes)
    #sys.stderr.write("%d tests pre-merging\n" % pre)
    while repeat:
        repeat = False
        for i in range(len(parse_graph.nodes)):
            if repeat:
                # Already merged something; indices are now off, so start over
                break
            for j in range(i):
                merged = TryMerge(i, j, finals)
                if merged:
                    del parse_graph.nodes[j] # (otherwise j would be off by one)
                    del parse_graph.edges[j]
                    del parse_graph.finals[j]
                    repeat = True
                    break
    #sys.stderr.write("%d tests post-merging\n" % len(parse_graph.nodes))
    diff = pre - len(parse_graph.nodes)
    if diff > 0:
        sys.stderr.write("%s: eliminated %d redundant tests (%d -> %d)\n" %
                (str(f), diff, pre, len(parse_graph.nodes)))

    for i in range(len(parse_graph.nodes)):
        contents["pipechecktest"] += "Alternative\n"
        for j in parse_graph.nodes[i].itervalues():
            contents["pipechecktest"] += str(j)
        for j in parse_graph.edges[i]:
            contents["pipechecktest"] += str(j)
        for j in parse_graph.finals[i]:
            if j in inits:
                continue;
            n = parse_graph.nodes[i][j]
            if n.addr in finals:
                final = Condition()
                final.addr = n.addr
                final.data = OnlyMemberOf(n.data)
                contents["pipechecktest"] += str(final)
    contents["pipechecktest"] += outcome

def ParseFinals(s):
    finals = set()
    for ln in s.split('\n'):
        if "exists" not in ln and "forall" not in ln:
            continue
        for i in re.findall(final_re, ln):
            if ':' in i[0]:
                continue
            # final = Condition()
            # final.addr = Addr(i[0])
            # final.data = Data(i[1])
            finals.add(Addr(i[0]))
        return finals

try:
    model = sys.argv[1]
    filename = sys.argv[2]
    unobserved = sys.argv[3]
    sc_model = sys.argv[4]
    assert sys.argv[5] in ["all", "po", "power"]
except IndexError:
    sys.stderr.write("Usage: python herd_to_pipecheck.py <cats model> <filename> <all | po>\n")
    sys.exit(1)

def CheckIfPermitted(model, filename, unobserved, sc_model):
    try:
        process = subprocess.Popen(
            ["herd", "-show", "prop", "-model", model, filename],
            stdout=subprocess.PIPE)
    except OSError:
        sys.stderr.write("Could not run herd.  Is herd in your path?\n")
        sys.exit(1)
    herd_output, _ = process.communicate()

    finals = ParseFinals(herd_output)

    if "Never" in herd_output:
        return "Forbidden\n", finals
    elif "Sometimes" in herd_output:
        # Outcome is permitted, but Permitted, Required, and Unobserved
        # all count as "permitted"
        filenamebase = os.path.splitext(filename)[0]
        if filenamebase in unobserved:
            return "Unobserved\n", finals
        process = subprocess.Popen(
            ["herd", "-show", "prop", "-model", sc_model, filename],
            stdout=subprocess.PIPE)
        herd_sc_output, _ = process.communicate()
        if "Never" in herd_sc_output:
            return "Permitted\n", finals
        elif "Sometimes" in herd_sc_output or "Always" in herd_sc_output:
            # Treat SC-legal outcomes as required
            return "Required\n", finals
        else:
            sys.stderr.write("Herd output:\n%s\n" % herd_sc_output)
            raise Exception("Could not parse herd output")
    elif "Always" in herd_output:
        return "Required\n", finals
    else:
        sys.stderr.write("Herd output:\n%s\n" % herd_output)
        raise Exception("Could not parse herd output")

def ParseUnobserved(f):
    unobserved = set()
    for ln in open(f, 'r'):
        if ln[-1] == "\n":
            ln = ln[:-1]
        unobserved.add(ln)
    return unobserved

def main(model, filename, unobserved, sc_model):
    # model: in this case C11_patialSC.cat
    # filename: .litmus file
    # unobserved: list of tests that were never observed on a given uarch, can be /dev/null
    # sc_model: sc.cat

    contents = {}				
    contents["filename"] = filename
    contents["pipechecktest"] = ""

    # Parse file listing unobserved outcomes
    unobserved = ParseUnobserved(unobserved)


    # Permitted/Forbidden
    outcome, finals = CheckIfPermitted(model, filename, unobserved, sc_model)
    contents["permitted"] = outcome == "Permitted"

    # Nodes and edges
    tmpdir = tempfile.mkdtemp()
    devnull = open(os.devnull, 'wb')
    subprocess.check_call([
        "herd", "-show", "prop", "-model", model, filename,
        "-through", "all", "-showinitrf", "true",
        "-showfinalrf", "true", "-q", "-o", tmpdir],
        stdout=devnull, stderr=devnull)
    with open(tmpdir + os.sep + os.path.basename(filename[:-6]) + "dot", 'r') as f:
        parse_graph(contents, f, finals, outcome)

    with open(filename[:-6] + "test", 'w') as f:
      f.write(contents["pipechecktest"])

main(model, filename, unobserved, sc_model) 	# all arguments from command line and parsed from argv

