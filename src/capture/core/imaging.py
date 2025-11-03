"""Imaging functions for CAPTURE pipeline."""

import logging
import casatasks as cts

def tclean_image(msfile, imagename, niter=0, threshold='1mJy', cell='1arcsec',
                imsize=1024, nterms=1, wprojplanes=1, robust=0.0):
    """Create an image using tclean."""
    if niter == 0:
        imagename = f"{imagename}-dirty-img"
    
    cts.tclean(
        vis=msfile,
        imagename=imagename,
        selectdata=True,
        field='0',
        spw='',
        imsize=imsize,
        cell=cell,
        robust=robust,
        weighting='briggs',
        specmode='mfs',
        nterms=nterms,
        niter=niter,
        usemask='auto-multithresh',
        minbeamfrac=0.1,
        sidelobethreshold=2.0,
        smallscalebias=0.6,
        threshold=threshold,
        aterm=True,
        pblimit=-0.001,
        pbmask=0.0,
        deconvolver='mtmfs' if nterms > 1 else 'multiscale',
        gridder='wproject',
        wprojplanes=wprojplanes,
        scales=[0, 5, 15],
        wbawp=False,
        restoration=True,
        savemodel='modelcolumn',
        cyclefactor=0.5,
        parallel=False,
        interactive=False
    )
    
    # Export to FITS format
    if nterms > 1:
        cts.exportfits(imagename=f"{imagename}.image.tt0", fitsimage=f"{imagename}.fits")
    else:
        cts.exportfits(imagename=f"{imagename}.image", fitsimage=f"{imagename}.fits")
    
    return imagename

def make_dirty_image(msfile, cell, imsize, nterms=1, wprojplanes=1, robust=0.0):
    """Create a dirty image."""
    nameprefix = msfile.split('/')[-1].split('.')[0]
    logging.info(f"Creating dirty image for {nameprefix}")
    
    return tclean_image(
        msfile=msfile,
        imagename=nameprefix,
        niter=0,
        cell=cell,
        imsize=imsize,
        nterms=nterms,
        wprojplanes=wprojplanes,
        robust=robust
    )

def clean_image(msfile, niter, threshold, cell, imsize, nterms=1, wprojplanes=1, robust=0.0):
    """Create a cleaned image."""
    nameprefix = msfile.split('/')[-1].split('.')[0]
    logging.info(f"Creating cleaned image for {nameprefix}")
    
    return tclean_image(
        msfile=msfile,
        imagename=nameprefix,
        niter=niter,
        threshold=threshold,
        cell=cell,
        imsize=imsize,
        nterms=nterms,
        wprojplanes=wprojplanes,
        robust=robust
    )
