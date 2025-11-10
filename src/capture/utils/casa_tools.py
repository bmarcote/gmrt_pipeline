"""CASA helper functions for CAPTURE pipeline."""

import os
import logging
from casatasks import flagdata, visstat
from casatools import ms
from casatools import msmetadata as msmd


def msmd_wrapper(func):
    """Decorator to handle msmd.open and msmd.done operations."""
    def wrapper(msfile, *args, **kwargs):
        try:
            openmsfile = msmd(msfile)
            openmsfile.open(msfile)
            result = func(msfile, *args, **kwargs)
        finally:
            openmsfile.close()
        return result
    return wrapper


def vislistobs(msfile):
    """Write verbose output of listobs task."""
    ms.open(msfile)
    outr = ms.summary(verbose=True, listfile=msfile+'.list')
    try:
        assert os.path.isfile(msfile+'.list')
        logging.info("Listobs output saved to .list file")
    except AssertionError:
        logging.info("Listobs output not saved to .list file. Check CASA log.")
    return outr

@msmd_wrapper
def getpols(msfile):
    """Get number of polarizations in file."""
    polid = msmd.ncorrforpol(0)
    return polid

@msmd_wrapper
def getfields(msfile):
    """Get list of field names in MS."""
    fieldnames = msmd.fieldnames()
    return fieldnames

@msmd_wrapper
def getscans(msfile, mysrc):
    """Get list of scan numbers for specified source."""
    return msmd.scansforfield(mysrc).tolist()

@msmd_wrapper
def getantlist(myvis, scanno):
    """Get list of antennas for given scan."""
    antenna_name = msmd.antennasforscan(scanno)
    antlist = []
    for i in range(0, len(antenna_name)):
        antlist.append(msmd.antennanames(antenna_name[i])[0])
    return antlist

@msmd_wrapper
def getnchan(msfile):
    """Get number of channels."""
    nchan = msmd.nchan(0)
    return nchan

@msmd_wrapper
def getbw(msfile):
    """Get bandwidth."""
    bw = msmd.bandwidths(0)
    return bw

@msmd_wrapper
def freq_info(ms_file):
    """Get frequency information."""
    sw = 0
    freq = msmd.chanfreqs(sw)
    return freq

def getbandcut(inpmsfile):
    """Get band-specific cutoff values."""
    cutoffs = {
        'L': 0.2, 'P': 0.3, '235': 0.5, '610': 0.2,
        'b4': 0.2, 'b2': 0.7, '150': 0.7
    }
    frange = freq_info(inpmsfile)
    fmin = min(frange)
    
    if fmin > 1000E06:
        fband = 'L'
    elif fmin > 500E06 and fmin < 1000E06:
        fband = 'b4'
    elif fmin > 260E06 and fmin < 560E06:
        fband = 'P'
    elif fmin > 210E06 and fmin < 260E06:
        fband = '235'
    elif fmin > 80E6 and fmin < 200E6:
        fband = 'b2'
    else:
        logging.error("Frequency band does not match any GMRT bands.")
        return None
        
    logging.info(f"Frequency band: {fband}")
    xcut = cutoffs.get(fband)
    logging.info(f"Mean cutoff for flagging bad antennas: {xcut}")
    return xcut

def myvisstatampraw(myfile, myspw, myant, mycorr, myscan):
    """Get visibility statistics."""
    mystat = visstat(
        vis=myfile, axis="amp", datacolumn="data", useflags=False,
        spw=myspw, selectdata=True, antenna=myant, correlation=mycorr,
        scan=myscan, reportingaxes="ddid"
    )
    mymean1 = mystat['DATA_DESC_ID=0']['mean']
    return mymean1

def flagsummary(msfile):
    """Print flagging summary."""
    try:
        assert os.path.isdir(msfile), "MS file not found."
    except AssertionError:
        logging.error("MS file not found.")
        return
        
    s = flagdata(vis=msfile, mode='summary')
    allkeys = s.keys()
    logging.info("Flagging percentage:")
    for x in allkeys:
        try:
            for y in s[x].keys():
                flagged_percent = 100.*(s[x][y]['flagged']/s[x][y]['total'])
                logstring = f"{x} {y} {flagged_percent}"
                logging.info(logstring)
        except AttributeError:
            pass
