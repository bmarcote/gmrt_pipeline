"""Calibration functions for CAPTURE pipeline."""

import logging
import casatasks as cts

def initial_calibration(msfile, ref_ant, flagspw, myampcals, mybpcals, mypcals, mycalsuffix=''):
    """Perform initial calibration steps."""
    logging.info("Starting initial calibration")
    
    # Clear calibration
    cts.clearcal(vis=msfile)
    
    # Set flux density scale
    for ampcal in myampcals:
        cts.setjy(vis=msfile, spw=flagspw, field=ampcal)
        
    # Delay calibration using first flux calibrator
    gntable = f"{msfile}.K1{mycalsuffix}"
    cts.gaincal(
        vis=msfile, caltable=gntable, spw=flagspw, field=myampcals[0],
        solint='60s', refant=ref_ant, solnorm=True, gaintype='K',
        gaintable=[], parang=True
    )
    
    # Initial bandpass calibration
    aptable = f"{msfile}.AP.G0{mycalsuffix}"
    cts.gaincal(
        vis=msfile, caltable=aptable, append=False, field=','.join(mybpcals),
        spw=flagspw, solint='int', refant=ref_ant, minsnr=2.0,
        solmode='L1R', gaintype='G', calmode='ap',
        gaintable=[gntable], interp=['nearest,nearestflag'], parang=True
    )
    
    bptable = f"{msfile}.B1{mycalsuffix}"
    cts.bandpass(
        vis=msfile, caltable=bptable, spw=flagspw, field=','.join(mybpcals),
        solint='inf', refant=ref_ant, solnorm=True, minsnr=2.0,
        fillgaps=8, parang=True,
        gaintable=[gntable, aptable],
        interp=['nearest,nearestflag', 'nearest,nearestflag']
    )
    
    return gntable, aptable, bptable

def gain_calibration(msfile, mycal, ref_ant, gainspw, uvrange, mycalsuffix, append=False):
    """Perform gain calibration."""
    gtable = [f"{msfile}.K1{mycalsuffix}", f"{msfile}.B1{mycalsuffix}"]
    
    cts.gaincal(
        vis=msfile, caltable=f"{msfile}.AP.G{mycalsuffix}", spw=gainspw,
        uvrange=uvrange, append=append, field=mycal, solint='120s',
        refant=ref_ant, minsnr=2.0, solmode='L1R', gaintype='G',
        calmode='ap', gaintable=gtable,
        interp=['nearest,nearestflag', 'nearest,nearestflag'],
        parang=True
    )
    
    return gtable

def apply_calibration(msfile, field, gaintables, gainfield=None, interp=None):
    """Apply calibration tables."""
    if gainfield is None:
        gainfield = [field, '', '']
    if interp is None:
        interp = ['nearest', '', '']
        
    cts.applycal(
        vis=msfile, field=field, gaintable=gaintables,
        gainfield=gainfield, interp=interp,
        calwt=False, parang=False
    )
