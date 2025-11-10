"""CASA helper functions for CAPTURE pipeline."""

import os
import logging
from pathlib import Path
from casatasks import flagdata, visstat
from casatools import ms
from casatools import msmetadata
from contextlib import contextmanager


@contextmanager
def msmd(msfile: str | Path, nomodify: bool = True, lock: str = 'default'):
    """Wrapper function that saves the user to do the shit thing that CASA developers coded,
    of loading the ms() then open, and not being save of closing it."""
    try:
        msobj = msmetadata()
        msobj.open(msfile if isinstance(msfile, str) else str(msfile), nomodify=nomodify,
                     lockoptions={'option': lock})
        yield msobj
    finally:
        msobj.done()
        msobj.close()

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

def getpols(msfile):
    """Get number of polarizations in file."""
    with msmd(msfile) as msmdfile:
        polid = msmdfile.ncorrforpol(0)

    return polid

def getfields(msfile):
    """Get list of field names in MS."""
    with msmd(msfile) as msmdfile:
        fieldnames = msmdfile.fieldnames()
    return fieldnames

def getscans(msfile, mysrc):
    """Get list of scan numbers for specified source."""
    with msmd(msfile) as msmdfile:
        return msmdfile.scansforfield(mysrc).tolist()

def getantlist(myvis, scanno):
    """Get list of antennas for given scan."""
    with msmd(myvis) as msmdfile:
        antenna_name = msmdfile.antennasforscan(scanno)
        antlist = []
        for i in range(0, len(antenna_name)):
            antlist.append(msmdfile.antennanames(antenna_name[i])[0])
    return antlist

def getnchan(msfile):
    """Get number of channels."""
    with msmd(msfile) as msmdfile:
        nchan = msmdfile.nchan(0)
    return nchan

def getbw(msfile):
    """Get bandwidth."""
    with msmd(msfile) as msmdfile:
        bw = msmdfile.bandwidths(0)
    return bw

def freq_info(ms_file):
    """Get frequency information."""
    with msmd(ms_file) as msmdfile:
        sw = 0
        freq = msmdfile.chanfreqs(sw)
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
