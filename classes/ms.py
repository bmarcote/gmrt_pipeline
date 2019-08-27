# -*- coding: utf-8 -*-
#
# Class that defines a Measurement Set (MS) object.
# It automatically reads the most relevant information from the MS that is
# required for CAGA. In this sense, it makes unnecessary to read that
# information everytime is needed and it avoids the user to know where
# that information is located inside the MS.
#
# @Author: Benito Marcote (bmarcote)
# @Email: marcote@jive.eu
# @Date:   2018-11-07
#
# @Last Modified by: bmarcote
# @Last Modified time: 2018-11-07
import os
import sys
import numpy as np
from collections import defaultdict
from casac import casac

class Ms(object):
    """Defines a MS (measurement set) object.
    It also reads some metadata and store them as attributes.
    """
    def __init__(self, mspath):
        # Get the basepath (folder where the file is located) and the file
        # and store them in path and msname, respectively.
        self._path
        self._msname
        if self.exists:
            self.get_metadata()


    @property
    def path(self):
        """Returns the path to the MS set."""
        return self._path

    @path.setter
    def path(self, newpath):
        self._path = newpath


    @property
    def msname(self):
        return self._msname


    @property
    def exists(self):
        return os.path.exists('{}/{}'.format(self.path, self.msname))


    @property
    def antennas(self):
        raise NotImplemented


    def has_antenna(self, antenna):
        return antenna in self.antennas


    @property
    def sources(self):
        return self._sources


    def has_source(self, source):
        return source in self.sources


    @property
    def channels(self):
        return self._channels


    @property
    def subbands(self):
        return self._subbands


    def get_metadata(self):
        assert self.exists
        msdata = casac.ms()
        msdata.open('{}/{}'.format(self.path, self.msname))
        self._channels = msdata.nchan(0)
        self._subbands = msdata.metadata().nspw()
        self._sources = msdata.metadata().fieldnames()
        # self._reffreq = ms.getspectralwindowinfo()[str(msinfo['subbands']//2)]['RefFreq'] # In Hz
        # self._inttime = ms.getscansummary()[str(a_key)]['0']['IntegrationTime']
        msdata.done()
    

    def get_scans(self, src):
        """Returns the list of scan numbers where the specified source was
        observed.
        """
        msdata = casa.ms()
        msdata.open('{}/{}'.format(self.path, self.msname))
        list_scans = msdata.scansforfield(src).to_list()
        msdata.done()
        return list_scans

