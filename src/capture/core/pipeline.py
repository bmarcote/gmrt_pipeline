"""Core pipeline functionality for CAPTURE."""

import logging
import os
import tomllib
from datetime import datetime
import casatasks as cts

from ..utils.casa_tools import vislistobs

class Pipeline:
    """Main CAPTURE pipeline class."""
    
    def __init__(self, config_file='config_capture.toml'):
        """Initialize pipeline with configuration."""
        self.setup_logging()
        self.load_config(config_file)
        
    def setup_logging(self):
        """Set up logging configuration."""
        self.logfile_name = datetime.now().strftime('capture_%H_%M_%S_%d_%m_%Y.log')
        logging.basicConfig(filename=self.logfile_name, level=logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger('').addHandler(console)
        
        logging.info("#" * 85)
        logging.info("You are using the CASA-6 compatible version of CAPTURE")
        logging.info("CAsa Pipeline-cum-Toolkit for Upgraded GMRT data REduction")
        logging.info("Developed at NCRA by Ruta Kale and Ishwara-Chandra C. H.")
        logging.info("Please cite: Kale and Ishwara Chandra, ExA, 2021, 51, 95")
        logging.info("#" * 85)
        logging.info(f"LOGFILE = {self.logfile_name}")
        logging.info(f"CASA_LOGFILE = casa-{self.logfile_name}")
        logging.info("#" * 85)

        self.casa_logfile = f'casa-{self.logfile_name}'
        cts.casalog.setlogfile(self.casa_logfile)

    def load_config(self, config_file):
        """Load configuration from TOML file."""
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)
        
        # Input settings
        self.fromlta = config['input']['from_lta']
        self.fromfits = config['input']['from_fits']
        self.frommultisrcms = config['input']['from_multisrc_ms']
        self.ltafile = config['input']['lta_file']
        self.gvbinpath = config['input']['gvbin_path']
        self.fits_file = config['input']['fits_file']
        self.msfilename = config['input']['ms_filename']
        
        # Output settings
        self.splitfilename = config['output']['split_filename']
        self.splitavgfilename = config['output']['split_avg_filename']
        
        # Flagging settings
        self.findbadants = config['flagging']['find_bad_ants']
        self.flagbadants = config['flagging']['flag_bad_ants']
        self.findbadchans = config['flagging']['find_bad_chans']
        self.flagbadfreq = config['flagging']['flag_bad_freq']
        self.flaginit = config['flagging']['flag_init']
        self.flagsplitfile = config['flagging']['flag_split_file']
        self.doflagavg = config['flagging']['flag_avg']
        
        # Calibration settings
        self.doinitcal = config['calibration']['do_init_cal']
        self.doflag = config['calibration']['do_flag']
        self.redocal = config['calibration']['redo_cal']
        self.setquackinterval = config['calibration']['quack_interval']
        self.ref_ant = config['calibration']['ref_ant']
        self.clipfluxcal = config['calibration']['clip_flux_cal']
        self.clipphasecal = config['calibration']['clip_phase_cal']
        self.cliptarget = config['calibration']['clip_target']
        self.clipresid = config['calibration']['clip_resid']
        self.uvracal = config['calibration']['uvr_acal']
        self.uvrascal = config['calibration']['uvr_ascal']
        
        # Imaging settings
        self.makedirty = config['imaging']['make_dirty']
        self.doselfcal = config['imaging']['do_selfcal']
        self.dosubbandselfcal = config['imaging']['do_subband_selfcal']
        self.chanavg = config['imaging']['chan_avg']
        self.subbandchan = config['imaging']['subband_chan']
        self.imcellsize = [config['imaging']['cell_size']]
        self.imsize_pix = config['imaging']['image_size']
        self.clean_robust = config['imaging']['clean_robust']
        self.scaloops = config['imaging']['scal_loops']
        self.pcaloops = config['imaging']['pcal_loops']
        self.mJythreshold = config['imaging']['mjy_threshold']
        self.scalsolints = config['imaging']['scal_solints']
        self.niter_start = config['imaging']['niter_start']
        self.use_nterms = config['imaging']['use_nterms']
        self.nwprojpl = config['imaging']['nwproj_pl']
        
        # Processing settings
        self.target = config['processing']['target']
        self.usetclean = config['processing']['use_tclean']

    def process_lta(self):
        """Process LTA file if specified."""
        if not self.fromlta:
            return
            
        logging.info("Converting lta to FITS.")
        if not os.path.isfile(self.ltafile):
            logging.error("LTA file not found.")
            return
            
        if not all(os.path.isfile(x) for x in self.gvbinpath):
            logging.error("listscan and gvfits executables not found.")
            return
            
        # Convert LTA to FITS
        os.system(f"{self.gvbinpath[0]} {self.ltafile}")
        if self.fits_file and self.fits_file != 'TEST.FITS':
            os.system(f"sed -i 's/TEST.FITS/{self.fits_file}/ {self.ltafile.split('.')[0]}.log")
            
        if not os.path.isfile(self.fits_file):
            if os.path.isfile('TEST.FITS'):
                self.fits_file = 'TEST.FITS'
            else:
                os.system(f"{self.gvbinpath[1]} {self.ltafile.split('.')[0]}.log")

    def process_fits(self):
        """Process FITS file if specified."""
        if not self.fromfits:
            return
            
        if not self.fits_file:
            if not os.path.isfile('TEST.FITS'):
                logging.error("No FITS file specified.")
                return
            self.fits_file = 'TEST.FITS'
            
        if not os.path.isfile(self.fits_file):
            logging.error(f"FITS file {self.fits_file} not found.")
            return
            
        # Import FITS to MS
        if not self.msfilename:
            self.msfilename = f"{self.fits_file}.MS"
            
        if not os.path.isdir(self.msfilename):
            cts.importgmrt(fitsfile=self.fits_file, vis=self.msfilename)
            
        # Create listobs output
        vislistobs(self.msfilename)
        logging.info("See .list file for MS information.")
