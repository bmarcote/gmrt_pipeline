"""
Snakemake workflow for CAPTURE pipeline
CAsa Pipeline-cum-Toolkit for Upgraded GMRT data REduction
"""

import os
from pathlib import Path
import tomllib

# Load configuration
configfile: "config_capture.toml"

# Import pipeline modules
from capture.core.pipeline import Pipeline
from capture.core.calibration import initial_calibration, apply_calibration
from capture.core.imaging import make_dirty_image, clean_image
from capture.utils.casa_tools import getfields

# Initialize pipeline to get configuration values
pipeline = Pipeline(config['config_file'] if 'config_file' in config else 'config_capture.toml')

# Define input/output paths from config
LTAFILE = pipeline.ltafile if pipeline.ltafile else "data.lta"
FITS_FILE = pipeline.fits_file if pipeline.fits_file else "data.fits"
MS_FILE = pipeline.msfilename if pipeline.msfilename else f"{FITS_FILE}.MS"
SPLIT_FILE = pipeline.splitfilename if pipeline.splitfilename else "split.ms"
SPLIT_AVG_FILE = pipeline.splitavgfilename if pipeline.splitavgfilename else "avg-split.ms"

# Define target rule based on configuration
def get_final_outputs():
    """Determine final outputs based on configuration."""
    outputs = []
    
    if pipeline.makedirty:
        outputs.append(f"{MS_FILE}-dirty-img.fits")
    
    if pipeline.doselfcal:
        outputs.append(f"{SPLIT_AVG_FILE}-selfcal.ms")
    
    if not outputs:
        # Default to MS if no imaging specified
        outputs.append(MS_FILE)
    
    return outputs

rule all:
    input:
        get_final_outputs()

# Rule: Convert LTA to FITS
rule lta_to_fits:
    input:
        lta = LTAFILE
    output:
        fits = FITS_FILE
    log:
        "logs/lta_to_fits.log"
    run:
        from capture.core.pipeline import Pipeline
        p = Pipeline(config['config_file'] if 'config_file' in config else 'config_capture.toml')
        p.process_lta()

# Rule: Import FITS to MS
rule fits_to_ms:
    input:
        fits = FITS_FILE
    output:
        ms = directory(MS_FILE),
        listobs = f"{MS_FILE}.list"
    log:
        "logs/fits_to_ms.log"
    run:
        from capture.core.pipeline import Pipeline
        p = Pipeline(config['config_file'] if 'config_file' in config else 'config_capture.toml')
        p.process_fits()

# Rule: Initial flagging
rule initial_flagging:
    input:
        ms = MS_FILE
    output:
        flagged = touch(f"{MS_FILE}.flagged")
    log:
        "logs/initial_flagging.log"
    run:
        import logging
        from casatasks import flagdata
        
        ms = str(input.ms)
        logging.info(f"Performing initial flagging on {ms}")
        
        # Flag first channel
        flagdata(vis=ms, mode='manual', spw='0:0', action='apply')
        
        # Quack flagging
        flagdata(vis=ms, mode='quack', quackinterval=pipeline.setquackinterval,
                quackmode='beg', action='apply')
        flagdata(vis=ms, mode='quack', quackinterval=pipeline.setquackinterval,
                quackmode='endb', action='apply')

# Rule: Find bad antennas
rule find_bad_antennas:
    input:
        ms = MS_FILE,
        flagged = f"{MS_FILE}.flagged"
    output:
        badants = f"{MS_FILE}.badants.txt"
    log:
        "logs/find_bad_antennas.log"
    run:
        import logging
        from capture.utils.casa_tools import getfields, getscans, getantlist
        
        ms = str(input.ms)
        logging.info(f"Finding bad antennas in {ms}")
        
        # Placeholder - actual implementation would go here
        with open(output.badants, 'w') as f:
            f.write("# Bad antennas list\n")

# Rule: Initial calibration
rule initial_calibration:
    input:
        ms = MS_FILE,
        flagged = f"{MS_FILE}.flagged"
    output:
        k1 = directory(f"{MS_FILE}.K1"),
        b1 = directory(f"{MS_FILE}.B1"),
        apg0 = directory(f"{MS_FILE}.AP.G0"),
        apg = directory(f"{MS_FILE}.AP.G"),
        fluxscale = directory(f"{MS_FILE}.fluxscale")
    log:
        "logs/initial_calibration.log"
    run:
        import logging
        from capture.utils.casa_tools import getfields
        import numpy as np
        from casatasks import setjy, gaincal, bandpass, fluxscale, applycal, clearcal
        
        ms = str(input.ms)
        logging.info(f"Performing initial calibration on {ms}")
        
        # Get field information
        fields = getfields(ms)
        stdcals = ['3C48', '3C147', '3C286', '0542+498', '1331+305', '0137+331']
        
        # Identify calibrators (simplified)
        myampcals = [f for f in fields if f in stdcals]
        mypcals = []  # Would load from vla-cals.list
        mybpcals = myampcals
        
        if myampcals:
            # Set flux scale
            clearcal(vis=ms)
            for cal in myampcals:
                setjy(vis=ms, field=cal)
            
            # Delay calibration
            gaincal(vis=ms, caltable=str(output.k1), field=myampcals[0],
                   solint='60s', refant=pipeline.ref_ant, gaintype='K',
                   parang=True)

# Rule: Post-calibration flagging
rule post_calibration_flagging:
    input:
        ms = MS_FILE,
        cal = f"{MS_FILE}.fluxscale"
    output:
        flagged = touch(f"{MS_FILE}.cal_flagged")
    log:
        "logs/post_cal_flagging.log"
    run:
        import logging
        from casatasks import flagdata
        
        ms = str(input.ms)
        logging.info(f"Post-calibration flagging on {ms}")
        
        # Clip flagging on corrected data
        flagdata(vis=ms, mode="clip", datacolumn="corrected",
                clipminmax=pipeline.clipfluxcal, action="apply")

# Rule: Recalibration
rule recalibration:
    input:
        ms = MS_FILE,
        flagged = f"{MS_FILE}.cal_flagged"
    output:
        k1 = directory(f"{MS_FILE}.K1recal"),
        b1 = directory(f"{MS_FILE}.B1recal"),
        fluxscale = directory(f"{MS_FILE}.fluxscalerecal")
    log:
        "logs/recalibration.log"
    run:
        import logging
        logging.info(f"Recalibration on {input.ms}")
        # Similar to initial calibration with 'recal' suffix

# Rule: Split target data
rule split_target:
    input:
        ms = MS_FILE,
        cal = f"{MS_FILE}.fluxscale"
    output:
        split = directory(SPLIT_FILE)
    log:
        "logs/split_target.log"
    run:
        from casatasks import mstransform
        from capture.utils.casa_tools import getfields, getgainspw
        
        ms = str(input.ms)
        logging.info(f"Splitting target data from {ms}")
        
        # Get target fields
        gainspw, _, _, _ = getgainspw(ms)
        
        # Split target
        mstransform(vis=ms, outputvis=str(output.split),
                   field='target', spw=gainspw,
                   datacolumn='corrected')

# Rule: Average split data
rule average_split:
    input:
        split = SPLIT_FILE
    output:
        avg = directory(SPLIT_AVG_FILE)
    log:
        "logs/average_split.log"
    run:
        from casatasks import mstransform
        
        logging.info(f"Averaging {input.split}")
        mstransform(vis=str(input.split), outputvis=str(output.avg),
                   chanaverage=True, chanbin=pipeline.chanavg,
                   datacolumn='data')

# Rule: Make dirty image
rule make_dirty_image:
    input:
        ms = SPLIT_AVG_FILE if pipeline.dosplitavg else MS_FILE
    output:
        image = f"{{ms}}-dirty-img.image.tt0" if pipeline.use_nterms > 1 else f"{{ms}}-dirty-img.image",
        fits = f"{{ms}}-dirty-img.fits"
    log:
        "logs/make_dirty_image.log"
    run:
        from capture.core.imaging import make_dirty_image
        
        make_dirty_image(
            msfile=str(input.ms),
            cell=pipeline.imcellsize[0],
            imsize=pipeline.imsize_pix,
            nterms=pipeline.use_nterms,
            wprojplanes=pipeline.nwprojpl,
            robust=pipeline.clean_robust
        )

# Rule: Self-calibration
rule selfcal:
    input:
        ms = SPLIT_AVG_FILE
    output:
        selfcal_ms = directory(f"{SPLIT_AVG_FILE}-selfcal.ms"),
        image = f"{SPLIT_AVG_FILE}-selfcal.fits"
    log:
        "logs/selfcal.log"
    run:
        import logging
        logging.info(f"Self-calibration on {input.ms}")
        # Self-calibration implementation would go here

# Utility rule to visualize workflow
rule dag:
    output:
        "workflow.pdf"
    shell:
        "snakemake --dag | dot -Tpdf > {output}"
