#!/usr/bin/env python3
"""Main entry point for CAPTURE pipeline."""

import os
import sys
import argparse
import logging
from pathlib import Path

from .core.pipeline import Pipeline

def setup_logging(debug=False):
    """Set up logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_args() -> dict:
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


def show_version():
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
    """Main entry point for the pipeline.
    """
    if show_version:
        show_version()
    
    setup_logging(debug)
    try:
        os.chdir(working_dir)
        logging.info(f"Changed working directory to: {working_dir}")
    except OSError as e:
        logging.error(f"Failed to change working directory: {e}")
        sys.exit(1)
    
    input_path = validate_config(input_file)
    logging.info(f"Using configuration file: {input_path}")
    
    try:
        # Initialize and run pipeline
        pipeline = Pipeline(input_path)
        
        # Process data based on configuration
        if pipeline.fromlta:
            pipeline.process_lta()
        if pipeline.fromfits:
            pipeline.process_fits()
        if pipeline.frommultisrcms:
            if not pipeline.msfilename:
                logging.error("MS filename not provided in configuration")
                sys.exit(1)
            if not os.path.isdir(pipeline.msfilename):
                logging.error(f"MS file not found: {pipeline.msfilename}")
                sys.exit(1)
        
        # Perform calibration and imaging steps based on configuration
        if pipeline.flaginit:
            logging.info("Performing initial flagging")
            # Add flagging steps
        
        if pipeline.doinitcal:
            logging.info("Performing initial calibration")
            # Add calibration steps
        
        if pipeline.makedirty:
            logging.info("Creating dirty image")
            # Add imaging steps
        
        if pipeline.doselfcal:
            logging.info("Performing self-calibration")
            # Add self-calibration steps
        
        logging.info("Pipeline processing completed successfully")
        
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
