

# To be renamed to calibration_functions.py

def import_lta(ltafile, outputms, listscanpath, gvfitspath):
    os.system('{} {}'.format(listscanpath, ltafile))
    # TODO: make this change in ltafile name universal for any name.
    os.system('{} {}'.format(gvfitspath, ltafile.split('.')[0]+'.log'))
    # TODO: check what is the output name from gvfits to call the function
    import_fits(ltafile.split('.')[0]+'.fits', outputms)


def import_fits(fitsfile, outputms):
    """Imports a GMRT datafile in FITS format to MS format.

    Parameters:
        - path : str
            The path to the FITS file to be imported.
        - outputms : str
            The name of the output MS file to be created.
    """
    default(importgmrt)
    importgmrt(fitsfile=fitsfile, vis=outputms)
    default(flagdata)
    fladata(vis=outputms, mode='clip', clipminmax=[0,20000.], field='',
            spw='0:0', antenna='',correlation='', action='apply',
            savepars=True, cmdreason='dummy', flagbackup=False)


def percent_to_channel(msdata, fraction):
    """CAGA allows the user to specify the spw to select in CASA format
    but also by specifying the percentage of edge channels to remove.
    In this case, a float is specified, and will result in a channel
    selection in the form:
         '{fraction*n_channels}~{(1-fraction)*n_channels}'
    where n_channels is the total number of channels of the data.

    For example, if the data contain 1024 channels, and fraction = 0.2,
    then the selection will be '205~819'.

    Parameters:
        msdata : ms.Ms
            Ms object containing the data where the spw selection will be
            applied.
        fraction : str or float
            The fraction of edge channels to be unselected from the data.
            Must be between 0.0 and 1.0, and will select all channels from
            percent_spw to 1-percent_spw.
            It also accepts a range (in CASA format): 0.3~0.8 for
            non-symmetric ranges.
    Returns:
        channel_selection : str
            A string in CASA format with the channel selection side e.g.
            '205~819'
            (NOTE: the spw selection is not included).
    """
    if isinstance(fraction, float):
        assert 0.0 < fraction < 1.0
        ch_min = int(np.ceil(msdata.channels*fraction))
        ch_max = int(np.floor(msdata.channels*(1.0-fraction)))
    elif '~' in fraction:
        f = fraction.split('~')
        assert len(f) == 2
        assert 0.0 <= f[0] < 1.0
        assert 0.0 < f[1] <= 1.0
        # NOTE: Multiple selections not supported
        ch_min = int(np.ceil(msdata.channels*float(f[0])))
        ch_max = int(np.floor(msdata.channels*float(f[1])))
    else:
        # It must be a float (but in str format)
        assert 0.0 < float(fraction) < 1.0
        ch_min = int(np.ceil(msdata.channels*float(fraction)))
        ch_max = int(np.floor(msdata.channels*(1.0-float(fraction))))

    return '{}~{}'.format(ch_min, ch_max)


def spw_process(msdata, spw_selection):
    """CAGA allows the user to specify the spw to select in CASA format
    but also by specifying the percentage of edge channels to remove.
    In this case, a float is specified, and will result in a channel
    selection in the form:
         '*:{fraction*n_channels}~{(1-fraction)*n_channels}'
    where n_channels is the total number of channels of the data.

    It also accepts a range (in CASA format): 0.3~0.8 for non-symmetric
    ranges.

    Parameters:
        msdata : ms.Ms
            Ms object containing the data where the spw selection will be
            applied.
        spw_selection : str
            The spw selection that apart of the traditional CASA format
            can contain a selection of channels by percentage. e.g.
            spw_selection = '*:0.2' or '1~2:0.2~0.9'.
            For a MS with 1024 channels, thefraction = 0.2 will select
            channels 205 to 819 (thus returning '*:205~819').
            In the second case only spw 1 and 2 will be selected and
            channels within 0.2*number_of_channels and 0.9*number_of_channels
    Returns:
        spw_selection : str
            A string in CASA format with the spw selection side e.g.
            '*:205~819'
    """
    if ':' in spw_selection:
        # Both subband and channel selection are included
        # Otherwise only subbands are specified.
        sb, ch = spw_selection.split(':')
        if '.' in ch:
            # Then channel selection is specified as percentage
            ch = percent_to_channel(msdata, ch)

        return ':'.join([sb, ch])

    # Do nothing as only subband selection is provided.
    return spw_selection



