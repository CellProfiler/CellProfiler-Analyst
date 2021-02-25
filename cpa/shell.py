#!/bin/bash
'''
Load a properties file, then start a shell with certain local
variables exposed.
'''


import code
import sys
from optparse import OptionParser
import cpa
import cpa.properties
import cpa.dbconnect

parser = OptionParser("usage: %prog [options] [PROPERTIES-FILE [COMMAND]]")
options, args = parser.parse_args()

if len(args) > 0:
    cpa.properties.LoadFile(sys.argv[1])

variables = {'cpa': cpa}

if len(args) == 2:
    interpreter = code.InteractiveInterpreter(locals=variables)
    interpreter.runsource(sys.argv[2])
else:
    code.interact(local=variables)
