from collections import defaultdict
import numpy as np
from casac import casac


# Flagging functions

# NOT NEEDED ANY MORE

def flagging(mode='casa', **kwargs):
    """Run a typical flagging process on the data.
    Two modes are supported:
      - casa : run the flagdata command from CASA
      - aoflagger : run the flagging program AOFlagger
    Options required for each of the mode can be parsed in as additional parameters.
    """
    if mode == 'casa':
        flagging_casa(**kwargs)
    elif mode == 'aoflagger':
        flagging_aoflagger(**kwargs)
    else:
        raise ValueError('The specified mode ({}) is not supported'.format(mode))


def flagging_aoflagger(**kwargs):
    """Perform a flagging on the data by running AOFlagger
    """
    raise NotImplemented


def flagging_casa(**kwargs):
    """Runs flagdata with all provided commands.
    """


