
import os
import sys
import glob
import shutil
import ConfigParser
import logging
import datetime
from collections import defaultdict
import numpy as np
# from casa import *
import casa


# Find the path of the pipeline and add it to the current path. There should only be one
this_file_argv = [argv for argv in sys.argv if 'main.py' in argv][0]
this_path = os.path.abspath(os.path.dirname(this_file_argv))

from src import ms
from src import casa_functions as cf
from src import general_functions as gf


# Here I import the input parameters as pars.
input_file = sys.argv[-1]

if not os.path.isfile(input_file):
    raise IOError("Input file {} not found.".format(input_file))


config = ConfigParser.ConfigParser()
config.read(input_file)

pars = defaultdict(dict)

for a_param in config.defaults():
    pars['DEFAULT'][a_param] = gf.evaluate(config.defaults()[a_param])

# source-related parameters must be a list of sources
for a_param in ('ampcalibrator', 'phaseref', 'target'):
    if type(pars['DEFAULT'][a_param]) is not list:
        # Only case: there is only one source
        pars['DEFAULT'][a_param] = [pars['DEFAULT'][a_param]]

for a_section in config.sections():
    for a_param in config.options(a_section):
        # Only those ones that are not in DEFAULTS
        # if a_param not in pars['DEFAULT']:
        pars[a_section][a_param] = gf.evaluate(config.get(a_section, a_param))

# Remove all values that were in DEFAULT but not in the section
config._defaults = {}
for a_section in config.sections():
    for a_param in tuple(pars[a_section]):
        if a_param not in config.options(a_section):
            pars[a_section].pop(a_param)


assert len(pars['DEFAULT']['solint']) == pars['DEFAULT']['pcycles']+pars['DEFAULT']['apcycles']+1


# Create the original MS
msdata = ms.Ms(pars['DEFAULT']['msfile'], pars['DEFAULT']['projectname'])

# Check that exists otherwise stop the pipeline.
assert msdata.exists



# Properly parse the spw values if exist
# if 'spw_flagging' in pars['DEFAULT']:
#     pars['DEFAULT']['spw_flagging'] = cf.spw_parse(msdata, pars['DEFAULT']['spw_flagging'])

# if 'spw_gaincal' in pars['DEFAULT']:
#     pars['DEFAULT']['spw_gaincal'] = cf.spw_parse(msdata, pars['DEFAULT']['spw_gaincal'])


# Create the basic structure of folders for the output of the pipeline
gf.create_directory_tree(pars)



pipeline_steps = gf.Steps().steps_to_perform(pars['DEFAULT']['steps'])

for a_stepfunction in pipeline_steps:
    a_stepfunction(msdata, pars)


print('The pipeline has ended.')
