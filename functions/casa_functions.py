

# To be renamed to calibration_functions.py


def import_lta():



def import_fits(path, outputms):
    """Imports a GMRT datafile in FITS format to MS format.

    Parameters:
        - path : str
            The path to the FITS file to be imported.
        - outputms : str
            The name of the output MS file to be created.
    """
    default(importgmrt)
    importgmrt(fitsfile=path, vis=outputms)
    default(flagdata)
    fladata(vis=outputms, mode='clip', clipminmax=[0,20000.], field='',
            spw='0:0', antenna='',correlation='', action='apply',
            savepars=True, cmdreason='dummy', flagbackup=False)






