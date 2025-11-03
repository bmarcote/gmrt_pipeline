"""Example script showing basic usage of CAPTURE package."""

from capture.core.pipeline import Pipeline
from capture.core.calibration import initial_calibration, apply_calibration
from capture.core.imaging import make_dirty_image, clean_image

def main():
    # Initialize pipeline with configuration
    pipeline = Pipeline('config_capture.ini')
    
    # Process data from LTA/FITS to MS format
    pipeline.process_lta()  # If starting from LTA
    pipeline.process_fits() # If starting from FITS
    
    # Get basic parameters
    msfile = pipeline.msfilename
    ref_ant = pipeline.ref_ant
    flagspw = '0:51~950'  # Example value, should come from configuration
    
    # Perform initial calibration
    gntable, aptable, bptable = initial_calibration(
        msfile=msfile,
        ref_ant=ref_ant,
        flagspw=flagspw,
        myampcals=['3C286'],  # Example calibrator
        mybpcals=['3C286'],   # Example bandpass calibrator
        mypcals=['J1924+3329'] # Example phase calibrator
    )
    
    # Apply calibration to calibrators
    apply_calibration(
        msfile=msfile,
        field='3C286',
        gaintables=[gntable, aptable, bptable]
    )
    
    # Apply calibration to target
    apply_calibration(
        msfile=msfile,
        field='mytarget',
        gaintables=[gntable, aptable, bptable],
        gainfield=['3C286', '', ''],
        interp=['linear', '', 'nearest']
    )
    
    # Create images
    make_dirty_image(
        msfile=msfile,
        cell='1arcsec',
        imsize=1024,
        nterms=2,
        wprojplanes=128,
        robust=0.0
    )
    
    clean_image(
        msfile=msfile,
        niter=1000,
        threshold='1mJy',
        cell='1arcsec',
        imsize=1024,
        nterms=2,
        wprojplanes=128,
        robust=0.0
    )

if __name__ == '__main__':
    main()
