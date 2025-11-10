"""Pipeline step definitions for CAPTURE."""

import logging
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class PipelineStep:
    """Represents a single step in the pipeline."""
    name: str
    function: Callable
    inputs: List[str]
    outputs: List[str]
    
    def get_input_paths(self, **config):
        """Get actual file paths for inputs based on configuration."""
        paths = []
        for inp in self.inputs:
            path = inp.format(**config)
            paths.append(path)
        return paths
    
    def get_output_paths(self, **config):
        """Get actual file paths for outputs based on configuration."""
        paths = []
        for out in self.outputs:
            path = out.format(**config)
            paths.append(path)
        return paths


def lta_to_fits_step(pipeline):
    """Convert LTA to FITS file."""
    pipeline.process_lta()


def fits_to_ms_step(pipeline):
    """Import FITS file to MS."""
    pipeline.process_fits()


def initial_flagging_step(pipeline):
    """Perform initial flagging."""
    from casatasks import flagdata
    from ..utils.casa_tools import flagsummary
    
    msfile = pipeline.msfilename
    logging.info(f"Performing initial flagging on {msfile}")
    
    # Flag first channel
    flagdata(vis=msfile, mode='manual', spw='0:0', action='apply')
    
    # Quack flagging
    flagdata(vis=msfile, mode='quack', 
            quackinterval=pipeline.setquackinterval,
            quackmode='beg', action='apply')
    flagdata(vis=msfile, mode='quack', 
            quackinterval=pipeline.setquackinterval,
            quackmode='endb', action='apply')
    
    flagsummary(msfile)


def initial_calibration_step(pipeline):
    """Perform initial calibration."""
    from ..core.calibration import initial_calibration, gain_calibration, apply_calibration
    from ..utils.casa_tools import getfields
    from casatasks import fluxscale
    
    msfile = pipeline.msfilename
    logging.info(f"Performing initial calibration on {msfile}")
    
    # Get field information
    fields = getfields(msfile)
    stdcals = ['3C48', '3C147', '3C286', '0542+498', '1331+305', '0137+331']
    
    # Identify calibrators
    myampcals = [f for f in fields if f in stdcals]
    mybpcals = myampcals
    mypcals = []
    
    if not myampcals:
        myampcals = [fields[0]]
        mybpcals = [fields[0]]
    
    flagspw = '0:1~511'
    
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
    fluxscale(
        vis=msfile,
        caltable=f"{msfile}.AP.G",
        fluxtable=f"{msfile}.fluxscale",
        reference=myampcals[0] if myampcals else '',
        incremental=False
    )
    
    # Apply calibration to all fields
    gaintables = [gntable, bptable, f"{msfile}.fluxscale"]
    for field in fields:
        apply_calibration(
            msfile=msfile,
            field=field,
            gaintables=gaintables
        )


def make_dirty_image_step(pipeline):
    """Create dirty image."""
    from ..core.imaging import make_dirty_image
    
    image_ms = pipeline.splitavgfilename if pipeline.chanavg > 1 else pipeline.splitfilename
    
    make_dirty_image(
        msfile=image_ms,
        cell=pipeline.imcellsize[0],
        imsize=pipeline.imsize_pix,
        nterms=pipeline.use_nterms,
        wprojplanes=pipeline.nwprojpl,
        robust=pipeline.clean_robust
    )


# Define all pipeline steps
PIPELINE_STEPS = {
    'lta_to_fits': PipelineStep(
        name='lta_to_fits',
        function=lta_to_fits_step,
        inputs=['{ltafile}'],
        outputs=['{fits_file}']
    ),
    'fits_to_ms': PipelineStep(
        name='fits_to_ms',
        function=fits_to_ms_step,
        inputs=['{fits_file}'],
        outputs=['{msfilename}', '{msfilename}.list']
    ),
    'initial_flagging': PipelineStep(
        name='initial_flagging',
        function=initial_flagging_step,
        inputs=['{msfilename}'],
        outputs=['{msfilename}.flagged']
    ),
    'initial_calibration': PipelineStep(
        name='initial_calibration',
        function=initial_calibration_step,
        inputs=['{msfilename}'],
        outputs=['{msfilename}.K1', '{msfilename}.B1', '{msfilename}.AP.G', '{msfilename}.fluxscale']
    ),
    'make_dirty_image': PipelineStep(
        name='make_dirty_image',
        function=make_dirty_image_step,
        inputs=['{splitfilename}'],
        outputs=['{splitfilename}-dirty-img.fits']
    )
}
