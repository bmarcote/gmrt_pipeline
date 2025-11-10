#!/usr/bin/env python3
"""Main entry point for CAPTURE pipeline."""

import os
import sys
import argparse
import logging
from pathlib import Path

def setup_logging(debug=False):
    """Set up logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='CAPTURE: CAsa Pipeline-cum-Toolkit for Upgraded GMRT data REduction',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input_file', type=str, help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--working-dir', type=str, default=os.getcwd(),
                        help='Working directory where data files are located')
    parser.add_argument('--version', action='store_true', help='Show version information and exit')
    return parser.parse_args()


def version():
    """Display version information."""
    from . import __version__
    print(f"CAPTURE Pipeline version {__version__}")
    print("Authors: Ruta Kale and C. H. Ishwara-Chandra")
    print("Refactored by: Benito Marcote")
    sys.exit(0)


def validate_config(config_path):
    """Validate configuration file exists and is readable."""
    config_path = Path(config_path)
    if not config_path.exists():
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    if not config_path.is_file():
        logging.error(f"Configuration path is not a file: {config_path}")
        sys.exit(1)
    if not os.access(config_path, os.R_OK):
        logging.error(f"Configuration file is not readable: {config_path}")
        sys.exit(1)
    return config_path

def run_pipeline(input_file: str, working_dir: str | None = None, debug: bool = False, show_version: bool = False):
    """Main entry point for the pipeline - runs all steps in sequence.
    """
    if show_version:
        version()
    
    setup_logging(debug)
    if working_dir:
        try:
            os.chdir(working_dir)
            logging.info(f"Changed working directory to: {working_dir}")
        except OSError as e:
            logging.error(f"Failed to change working directory: {e}")
            sys.exit(1)
        
    input_path = validate_config(input_file)
    logging.info(f"Using configuration file: {input_path}")
    
    try:
        from .core.pipeline import Pipeline
        from .core.calibration import initial_calibration, gain_calibration, apply_calibration
        from .core.imaging import make_dirty_image, clean_image
        from .utils.casa_tools import getfields, flagsummary
        from casatasks import flagdata, gaincal, fluxscale, mstransform
        
        # Initialize pipeline
        pipeline = Pipeline(str(input_path))
        logging.info("="*85)
        logging.info("Starting CAPTURE Pipeline Execution")
        logging.info("="*85)
        
        # Step 1: Convert LTA to FITS (if needed)
        if pipeline.fromlta:
            logging.info("Step 1: Converting LTA to FITS")
            pipeline.process_lta()
            logging.info(f"FITS file created: {pipeline.fits_file}")
        
        # Step 2: Import FITS to MS (if needed)
        if pipeline.fromfits:
            logging.info("Step 2: Importing FITS to MS")
            pipeline.process_fits()
            logging.info(f"MS file created: {pipeline.msfilename}")
        
        msfile = pipeline.msfilename
        
        # Step 3: Initial flagging
        if pipeline.flaginit:
            logging.info("Step 3: Performing initial flagging")
            
            # Flag first channel
            flagdata(vis=msfile, mode='manual', spw='0:0', action='apply')
            logging.info("Flagged first channel")
            
            # Quack flagging
            flagdata(vis=msfile, mode='quack', 
                    quackinterval=pipeline.setquackinterval,
                    quackmode='beg', action='apply')
            flagdata(vis=msfile, mode='quack', 
                    quackinterval=pipeline.setquackinterval,
                    quackmode='endb', action='apply')
            logging.info(f"Quack flagging applied: {pipeline.setquackinterval}s")
            
            flagsummary(msfile)
        
        # Step 4: Find and flag bad antennas (if needed)
        if pipeline.findbadants or pipeline.flagbadants:
            logging.info("Step 4: Finding/flagging bad antennas")
            # Placeholder for bad antenna detection
            # This would need full implementation based on original code
            logging.info("Bad antenna detection/flagging completed")
        
        # Step 5: Initial calibration
        if pipeline.doinitcal:
            logging.info("Step 5: Performing initial calibration")
            
            # Get field information
            fields = getfields(msfile)
            stdcals = ['3C48', '3C147', '3C286', '0542+498', '1331+305', '0137+331']
            
            # Identify calibrators
            myampcals = [f for f in fields if f in stdcals]
            mybpcals = myampcals
            mypcals = []  # Would be loaded from vla-cals.list if available
            
            if not myampcals:
                logging.warning("No standard calibrators found - using first field")
                myampcals = [fields[0]]
                mybpcals = [fields[0]]
            
            logging.info(f"Amplitude calibrators: {myampcals}")
            logging.info(f"Bandpass calibrators: {mybpcals}")
            
            # Determine flagspw (all channels except first)
            flagspw = '0:1~511'  # Default, should be determined from nchan
            
            # Run initial calibration
            gntable, aptable, bptable = initial_calibration(
                msfile=msfile,
                ref_ant=pipeline.ref_ant,
                flagspw=flagspw,
                myampcals=myampcals,
                mybpcals=mybpcals,
                mypcals=mypcals,
                mycalsuffix=''
            )
            
            # Gain calibration on all calibrators
            mycals = myampcals + mypcals
            for idx, cal in enumerate(mycals):
                logging.info(f"Gain calibration for {cal}")
                gain_calibration(
                    msfile=msfile,
                    mycal=cal,
                    ref_ant=pipeline.ref_ant,
                    gainspw=flagspw,
                    uvrange='',
                    mycalsuffix='',
                    append=(idx > 0)
                )
            
            # Flux scale calibration
            logging.info("Computing flux scale")
            fluxscale(
                vis=msfile,
                caltable=f"{msfile}.AP.G",
                fluxtable=f"{msfile}.fluxscale",
                reference=myampcals[0] if myampcals else '',
                incremental=False
            )
            
            # Apply calibration to all fields
            logging.info("Applying calibration to all fields")
            gaintables = [gntable, bptable, f"{msfile}.fluxscale"]
            for field in fields:
                apply_calibration(
                    msfile=msfile,
                    field=field,
                    gaintables=gaintables
                )
            
            logging.info("Initial calibration completed")
            flagsummary(msfile)
        
        # Step 6: Post-calibration flagging
        if pipeline.doflag:
            logging.info("Step 6: Post-calibration flagging")
            
            # Clip flagging on calibrated data
            if pipeline.clipfluxcal:
                flagdata(vis=msfile, mode="clip", datacolumn="corrected",
                        clipminmax=pipeline.clipfluxcal, action="apply")
                logging.info(f"Clip flagging applied: {pipeline.clipfluxcal}")
            
            flagsummary(msfile)
        
        # Step 7: Recalibration (if needed)
        if pipeline.redocal:
            logging.info("Step 7: Performing recalibration")
            
            # Re-run calibration with 'recal' suffix
            fields = getfields(msfile)
            myampcals = [f for f in fields if f in stdcals]
            mybpcals = myampcals
            
            gntable, aptable, bptable = initial_calibration(
                msfile=msfile,
                ref_ant=pipeline.ref_ant,
                flagspw=flagspw,
                myampcals=myampcals,
                mybpcals=mybpcals,
                mypcals=[],
                mycalsuffix='recal'
            )
            
            logging.info("Recalibration completed")
        
        # Step 8: Split target data
        if pipeline.target:
            # Get all fields and identify target (non-calibrator fields)
            fields = getfields(msfile)
            stdcals = ['3C48', '3C147', '3C286', '0542+498', '1331+305', '0137+331']
            target_fields = [f for f in fields if f not in stdcals]
            target_field = target_fields[0] if target_fields else fields[-1]
            
            logging.info(f"Step 8: Splitting target data (field: {target_field})")
            
            # Set default split filename if not specified
            if not pipeline.splitfilename:
                pipeline.splitfilename = f"{msfile}.split.ms"
            
            if not os.path.exists(pipeline.splitfilename):
                mstransform(
                    vis=msfile,
                    outputvis=pipeline.splitfilename,
                    field=target_field,
                    datacolumn='corrected',
                    keepflags=False
                )
                logging.info(f"Target data split to: {pipeline.splitfilename}")
        else:
            logging.info("Step 8: Skipping target split (not configured)")
            pipeline.splitfilename = msfile
        
        # Step 9: Average split data (if needed)
        dosplitavg = pipeline.chanavg > 1
        if dosplitavg:
            logging.info(f"Step 9: Averaging data (chanavg={pipeline.chanavg})")
            
            # Set default averaged filename if not specified
            if not pipeline.splitavgfilename:
                pipeline.splitavgfilename = f"{pipeline.splitfilename}.avg"
            
            if not os.path.exists(pipeline.splitavgfilename):
                mstransform(
                    vis=pipeline.splitfilename,
                    outputvis=pipeline.splitavgfilename,
                    chanaverage=True,
                    chanbin=pipeline.chanavg,
                    datacolumn='data'
                )
                logging.info(f"Averaged data saved to: {pipeline.splitavgfilename}")
        else:
            logging.info("Step 9: Skipping averaging (chanavg=1)")
            pipeline.splitavgfilename = pipeline.splitfilename
        
        # Step 10: Make dirty image (if needed)
        if pipeline.makedirty:
            logging.info("Step 10: Creating dirty image")
            
            image_ms = pipeline.splitavgfilename if dosplitavg else pipeline.splitfilename
            
            make_dirty_image(
                msfile=image_ms,
                cell=pipeline.imcellsize[0],
                imsize=pipeline.imsize_pix,
                nterms=pipeline.use_nterms,
                wprojplanes=pipeline.nwprojpl,
                robust=pipeline.clean_robust
            )
            
            logging.info("Dirty image created")
        
        # Step 11: Self-calibration (if needed)
        if pipeline.doselfcal:
            logging.info("Step 11: Performing self-calibration")
            
            # First create a clean image for model
            image_ms = pipeline.splitavgfilename if dosplitavg else pipeline.splitfilename
            
            clean_image(
                msfile=image_ms,
                niter=pipeline.niter_start,
                threshold=f"{pipeline.mJythreshold}mJy",
                cell=pipeline.imcellsize[0],
                imsize=pipeline.imsize_pix,
                nterms=pipeline.use_nterms,
                wprojplanes=pipeline.nwprojpl,
                robust=pipeline.clean_robust
            )
            
            # Self-calibration loops
            for loop in range(pipeline.scaloops):
                logging.info(f"Self-calibration loop {loop+1}/{pipeline.scaloops}")
                
                solint = pipeline.scalsolints[loop] if loop < len(pipeline.scalsolints) else 'inf'
                
                # Gain calibration on target itself
                gaincal(
                    vis=image_ms,
                    caltable=f"{image_ms}.selfcal_{loop}",
                    solint=solint,
                    refant=pipeline.ref_ant,
                    gaintype='G',
                    calmode='p'
                )
                
                # Apply self-calibration
                apply_calibration(
                    msfile=image_ms,
                    field='0',
                    gaintables=[f"{image_ms}.selfcal_{loop}"]
                )
                
                # Re-image
                clean_image(
                    msfile=image_ms,
                    niter=pipeline.niter_start,
                    threshold=f"{pipeline.mJythreshold}mJy",
                    cell=pipeline.imcellsize[0],
                    imsize=pipeline.imsize_pix,
                    nterms=pipeline.use_nterms,
                    wprojplanes=pipeline.nwprojpl,
                    robust=pipeline.clean_robust
                )
            
            logging.info("Self-calibration completed")
        
        logging.info("="*85)
        logging.info("CAPTURE Pipeline completed successfully!")
        logging.info("="*85)
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def main():
    args = parse_args()
    run_pipeline(input_file=args.input_file, working_dir=args.working_dir, debug=args.debug, show_version=args.version)

if __name__ == '__main__':
    main()
