# -*- coding: utf-8 -*-
#
# Class that defines a Measurement Set (MS) object.
# It automatically reads the most relevant information from the MS that is
# required for CAGA. In this sense, it makes unnecessary to read that
# information everytime is needed and it avoids the user to know where
# that information is located inside the MS.
#
# @Author: Benito Marcote
# @Email: marcote@jive.eu
# @Date:   2018-11-07
#
# @Last Modified by: bmarcote
# @Last Modified time: 2018-11-07
import os
import sys
import numpy as np
import datetime as dt
# from pyrap import tables as pt
# from collections import defaultdict
from casac import casac


class Subbands(object):
    """Defines the frequency setup of a given observation with the following data:
        - n_subbands : float
            Number of subbands.
        - channels : array-like
            Number of channels per subband (N-array, with N number of subbands).
        - freqs : array-like
            Reference frequency for each channel and subband (NxM array, with N
            number of subbands, and M number of channels per subband).
        - bandwidths : array-like
            Total bandwidth for each subband (N array, with N number of subbands).

    """
    @property
    def n_subbands(self):
        return self._n_subbands

    @property
    def channels(self):
        return self._channels

    @property
    def freqs(self):
        return self._freqs

    @property
    def bandwidths(self):
        return self._bandwidths

    def __init__(self, chans, freqs, bandwidths):
        """Inputs:
            - chans : array-like
                Number of channels per subband (N-array, with N number of subbands).
            - freqs : array-like
                Reference frequency for each channel and subband (NxM array, M number
                of channels per subband.
            - bandwidths : array-like
                Total bandwidth for each subband (N array, with N number of subbands).
        """
        self._n_subbands = len(chans)
        assert self._n_subbands == len(bandwidths)
        assert freqs.shape == (self._n_subbands, chans[0])
        self._channels = np.copy(chans)
        self._freqs = np.copy(freqs)
        self._bandwidths = np.copy(bandwidths)
        self._calibration_table_list = []



class Ms(object):
    """Defines a MS (measurement set) object.
    It also reads some metadata and store them as attributes.
    """
    def __init__(self, msfile, msname):
        # Get the basepath (folder where the file is located) and the file
        # and store them in path and msname, respectively.
        self._msfile = msfile
        # TODO: msname should be the name of the MS file (without extension, without path)
        self._msname = msname
        self._calibration_table_list = []
        if self.exists:
            self.get_metadata()
        else:
            print('WARNING: MS file {} does not exist. No metadata have been retrieved.'.format(self.msfile))


    @property
    def msfile(self):
        """Returns the file (with path) to the MS set."""
        return self._msfile

    @msfile.setter
    def msfile(self, newfile):
        self._msfile = newfile


    @property
    def msname(self):
        return self._msname


    @property
    def exists(self):
        return os.path.exists(self.msfile)


    @property
    def antennas(self):
        return self._antennas


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


    @property
    def reffreq(self):
        return self._reffreq


    @property
    def bandwidth(self):
        return self._bandwidth


    @property
    def num_corr(self):
        return self._ncorr


    @property
    def calibration_tables(self):
        return self._calibration_table_list


    def add_calibration_table(self, new_caltable):
        self._calibration_table_list.append(new_caltable)


    def get_metadata(self):
        assert self.exists
        msdata = casac.ms()
        msdata.open(self.msfile)
        spwinfo = msdata.getspectralwindowinfo()['0']
        self._channels = spwinfo['NumChan']
        self._reffreq = spwinfo['RefFreq']
        self._bandwidth = spwinfo['TotalWidth']
        self._ncorr = spwinfo['NumCorr']
        metadata = msdata.metadata()
        self._subbands = metadata.nspw()
        self._sources = metadata.fieldnames()
        self._antennas = metadata.antennanames()
        msdata.done()


    def scans(self, field):
        """Returns the list of scan numbers where the specified source was
        observed.
        """
        msdata = casac.ms()
        msdata.open(self.msfile)
        list_scans = msdata.metadata().scansforfield(field)
        msdata.done()
        return list_scans



