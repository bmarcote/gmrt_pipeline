# -*- coding: utf-8 -*-

# Functions used in CASA related to the data
# (e.g. calibration, flagging, inspection, etc).
#
# @Author: Benito Marcote
# @Email: marcote@jive.eu
#
# @Last Modified by: Marcote
# @Last Modified time: 2018-11-07

import os
import sys
import shutil
import subprocess
import casa
import ms
import numpy as np
from recipes import tec_maps
import flagging as flag

def import_lta(ltafile, outputms, listscanpath, gvfitspath):
    raise NotImplemented
    # os.system('{} {}'.format(listscanpath, ltafile))
    # # TODO: make this change in ltafile name universal for any name.
    # os.system('{} {}'.format(gvfitspath, ltafile.split('.')[0]+'.log'))
    # # TODO: check what is the output name from gvfits to call the function
    # import_fits(ltafile.split('.')[0]+'.fits', outputms)


def import_fits(fitsfile, outputms):
    """Imports a GMRT datafile in FITS format to MS format.

    Parameters:
        - path : str
            The path to the FITS file to be imported.
        - outputms : str
            The name of the output MS file to be created.
    """
    raise NotImplemented
    # default(casa.importgmrt)
    # casa.importgmrt(fitsfile=fitsfile, vis=outputms)
    # default(casa.flagdata)
    # casa.flagdata(vis=outputms, mode='clip', clipminmax=[0,20000.], field='',
    #         spw='0:0', antenna='',correlation='', action='apply',
    #         savepars=True, cmdreason='dummy', flagbackup=False)


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


def spw_parse(msdata, spw_selection):
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
    # TODO: It will break with complex syntaxes...
    if type(spw_selection) is float:
        return '*:{}'.format(percent_to_channel(msdata, spw_selection))
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


def data_inspection(msdata, params):
    casa.listobs(msdata.msfile, listfile=params['inspection']['listobs_outputfile'], overwrite=True)
    casa.plotants(msdata.msfile, figfile=params['inspection']['plotant_outputfile'], showgui=False)



def caltablename(aname, params):
    """Returns the path (including file name) of the caltable called "aname" by following
    the given paths where these files are supposed to be located.
    """
    return params['DEFAULT']['outdir'] + '/caltables/' + aname


def get_existing_caltables(msdata, params):
    """Checks if there are existing CASA calibration tables in the expected directory.
    If any, they will be imported into the msdata.
    """
    # NOTE: the idea is to import all of them. If the function re-runs again, then the table will be
    # re-created again, but will not be added a second time to the list of existing caltables.
    # So everything will hapily work.... If I am consistent.
    # TODO: Is it properly working?
    for a_calname in ('gain_K', 'gain_G', 'bandpass', 'gain_K2', 'gain_G2', 'fluxscale'):
        if os.path.exists(caltablename(a_calname, params)):
            msdata.add_calibration_tables = caltablename(a_calname, params)


def ionospheric_calibration(msdata, params):
    """Performs ionospheric corrections
    """
    tec_maps.create(vis=msdata.msfile, doplot=False, imname='ionospheric.maps')
    # Removes the previous calibration table if it exists
    if os.path.exists(caltablename('cal_ionos', params)):
        shutil.rmtree(caltablename('cal_ionos', params))

    gencal(vis=msdata.msfile, caltable=caltable('cal_ionos', params), caltype='tecim',
           infile='ionospheric.maps.IGS_TEC.im')

    if caltablename('cal_ionos', params) not in msdata.calibration_tables:
        msdata.add_calibration_table(caltablename('cal_ionos', params))


def initial_calibration(msdata, params):
    """Performs the standard calibration on GMRT data, which contains the following steps:
    - setjy
    - gaincal (K, i.e. delay fit)
    - gaincal (G, gains)
    Adds the created calibration tables to the currnent MS object.
    """
    calibration(msdata, params, ext='')


def second_calibration(msdata, params):
    """Performs the standard calibration on GMRT data, which contains the following steps:
    - setjy
    - gaincal (K, i.e. delay fit)
    - gaincal (G, gains)
    Adds the created calibration tables to the currnent MS object.
    It assumes that this is a second pass so it will append a '2' at the end of each created
    calibration table.
    """
    calibration(msdata, params, ext='2')


def calibration(msdata, params, ext=''):
    """Performs the standard calibration on GMRT data, which contains the following steps:
    - setjy
    - gaincal (K, i.e. delay fit)
    - gaincal (G, gains)
    Adds the created calibration tables to the currnent MS object.
    'ext' is a suffix that can be placed at the end of each calibration table name.
    """
    casa.setjy(vis=msdata.msfile, field=','.join(params['DEFAULT']['ampcalibrator']), **params['setjy'])

    # TODO: This should be a decorator of the casa function.
    # Remove the previous calibration if already exists
    if os.path.exists(caltablename('gain_K'+ext, params)):
        shutil.rmtree(caltablename('gain_K'+ext, params))

    # Tricky point: if the table is already in the list, then I will load
    # all previous calibration tables. Otherwise, all the ones in the list.
    if caltablename('gain_K'+ext, params) in msdata.calibration_tables:
        prev_caltables = msdata.calibration_tables[:msdata.calibration_tables.index(caltablename('gain_K'+ext,
                                                                                                 params))]
    else:
        prev_caltables = msdata.calibration_tables

    casa.gaincal(vis=msdata.msfile, caltable=caltablename('gain_K'+ext, params), calmode='ap',
            field=','.join(params['DEFAULT']['ampcalibrator']), gaintable=prev_caltables, **params['gaincal_K'])

    if caltablename('gain_K'+ext, params) not in msdata.calibration_tables:
        msdata.add_calibration_table(caltablename('gain_K'+ext, params))

    # Same for G gain cal.
    if os.path.exists(caltablename('gain_G'+ext, params)):
        shutil.rmtree(caltablename('gain_G'+ext, params))

    # Tricky point: if the table is already in the list, then I will load
    # all previous calibration tables. Otherwise, all the ones in the list.
    if caltablename('gain_G'+ext, params) in msdata.calibration_tables:
        prev_caltables = msdata.calibration_tables[:msdata.calibration_tables.index(caltablename('gain_G'+ext,
                                                                                                 params))]
    else:
        prev_caltables = msdata.calibration_tables

    # If phase-referencing observation
    if params['DEFAULT']['phaseref'] is not None:
        cals = params['DEFAULT']['ampcalibrator'] + params['DEFAULT']['phaseref']
    else:
        cals = params['DEFAULT']['ampcalibrator'] + params['DEFAULT']['target']

    casa.gaincal(vis=msdata.msfile, caltable=caltablename('gain_G'+ext, params), calmode='ap',
                 field=','.join(cals), gaintable=prev_caltables, **params['gaincal_G'])

    if caltablename('gain_G'+ext, params) not in msdata.calibration_tables:
        msdata.add_calibration_table(caltablename('gain_G'+ext, params))


def bandpass_calibration(msdata, params):
    """Performs the bandpass calibration on the ampcalibrator sources.
    """
    if os.path.exists(caltablename('bandpass', params)):
        shutil.rmtree(caltablename('bandpass', params))

    if caltablename('bandpass', params) in msdata.calibration_tables:
        prev_caltables = msdata.calibration_tables[:msdata.calibration_tables.index(caltablename('bandpass',
                                                                                                 params))]
    else:
        prev_caltables = msdata.calibration_tables

    casa.bandpass(vis=msdata.msfile, caltable=caltablename('bandpass', params),
                  field=','.join(params['DEFAULT']['ampcalibrator']), gaintable=prev_caltables,
                  **params['bpass'])

    if caltablename('bandpass', params) not in msdata.calibration_tables:
        msdata.add_calibration_table(caltablename('bandpass', params))


def fluxscale_calibration(msdata, params):
    """Performs the flux scale calibration.
    """
    if os.path.exists(caltablename('fluxscale', params)):
        shutil.rmtree(caltablename('fluxscale', params))

    if caltablename('fluxscale', params) in msdata.calibration_tables:
        prev_caltables = msdata.calibration_tables[:msdata.calibration_tables.index(caltablename('fluxscale',
                                                                                                 params))]
    else:
        prev_caltables = msdata.calibration_tables

    if params['DEFAULT']['phaseref'] is not None:
        transfer_sources = ','.join(params['DEFAULT']['phaseref'])
    else:
        transfer_sources = ','.join(params['DEFAULT']['target'])

    # Needs to use the latest G table in the list
    last_G_table = None
    for caltable in prev_caltables[::-1]:
        if 'gain_G' in caltable:
            last_G_table = caltable
            break

    if last_G_table is None:
        raise ValueError('No calibration G table found before fluxscale.')

    casa.fluxscale(vis=msdata.msfile, caltable=last_G_table, fluxtable=caltablename('fluxscale', params),
                   reference=','.join(params['DEFAULT']['ampcalibrator']),
                   transfer=transfer_sources, **params['fluxscale'])

    if caltablename('fluxscale', params) not in msdata.calibration_tables:
        msdata.add_calibration_table(caltablename('fluxscale', params))



def apply_calibration(msdata, params):
    """Apply all existing calibration tables to the data.
    """
    for a_bpass in params['DEFAULT']['ampcalibrator']:
        gainfield = ['']*len(msdata.calibration_tables)
        gainfield[msdata.calibration_tables.index(caltablename('fluxscale', params))] = a_bpass
        casa.applycal(vis=msdata.msfile, field=a_bpass, gaintable=msdata.calibration_tables, gainfield=gainfield,
                 **params['applycal'])

    if params['DEFAULT']['phaseref'] is not None:
        gainfield = ['']*len(msdata.calibration_tables)
        gainfield[msdata.calibration_tables.index(caltablename('fluxscale', params))] = ','.join(params['DEFAULT']['phaseref'])
        casa.applycal(vis=msdata.msfile, field=','.join(params['DEFAULT']['phaseref']),
                 gaintable=msdata.calibration_tables, gainfield=gainfield, **params['applycal'])

    casa.applycal(vis=msdata.msfile, field=','.join(params['DEFAULT']['target']),
             gaintable=msdata.calibration_tables, gainfield=gainfield, **params['applycal'])



def split_sources(msdata, params):
    """Splits all the sources with the corrected data.
    """
    for a_source in msdata.sources:
        # Path where it will be stored
        path2split = "{}/{}".format(params['DEFAULT']['outdir'], a_source)
        # Check that the directory exists
        if not os.path.exists(path2split):
            os.makedirs(path2split)

        splitfile = "{}/{}.split.ms".format(path2split, a_source)
        if os.path.exists(splitfile):
            shutil.rmtree(splitfile)

        # Remove the SPLIT file if exists
        casa.split(msdata.msfile, outputvis=splitfile, field=a_source, **params['split'])



def cleaning(splitdata, params, imagename):
    """Runs tclean on the given splitdata.
    """
    if os.path.exists(imagename+'*'):
        shutil.rmtree(imagename+'*')

    casa.tclean(splitdata.msfile, imagename=imagename, **params['tclean'])


def wscleaning(splitdata, params, imagename):
    """Runs WSClean to obtain an image from the calibrated data.
    """
    if os.path.exists(imagename+'*'):
        shutil.rmtree(imagename+'*')

    # try:
    options = '-name {}'.format(imagename)
    if isinstance(params['wsclean']['size'], float):
        params['wsclean']['size'] = '{0} {0}'.format(params['wsclean']['size'])
    for a_key in params['wsclean']:
        options += ' -{} {}'.format(a_key, params['wsclean'][a_key])

    print('Executing wsclean {} {}'.format(options, splitdata.msfile))
    proc = subprocess.Popen('wsclean {} {}'.format(options, splitdata.msfile), shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open('output-wsclean.log', 'a+') as wsclean_logfile:
        while proc.poll() is None:
            out = proc.stdout.read().decode('utf-8')
            out = proc.stdout.read().decode()
            sys.stdout.write(out)
            wsclean_logfile.write(out)
            sys.stdout.flush()

    # except:
    #     raise NotImplemented('WSClean program not found.')


def imaging(msdata, params):
    """Runs the cleaning process on all calibrated sources.
    """
    # TODO: to parallelize
    for a_source in msdata.sources:
        # splitfile = "{}/{}/{}.split.ms".format(params['DEFAULT']['outdir'], a_source, a_source)
        splitfile = "{}.split.ms".format(a_source)
        os.chdir("{}/{}/".format(params['DEFAULT']['outdir'], a_source))
        try:
            splitdata = ms.Ms(splitfile, a_source)
            imagename = splitdata.msfile.replace('.ms', '.{}'.format(params['DEFAULT']['useclean']))
            if splitdata.exists:
                if params['DEFAULT']['useclean'] == 'tclean':
                    cleaning(splitdata, params, imagename)
                elif params['DEFAULT']['useclean'] == 'wsclean':
                    wscleaning(splitdata, params, imagename)
                else:
                    raise ValueError('Value {} in useclean not known.'.format(params['DEFAULT']['useclean']))
            else:
                print('WARNING: {} does not exist. Images not produced.'.format(splitdata.msfile))

        finally:
            os.chdir("../")


def selfcalibration(splitdata, params, extname, calmode, solint):
    """Given an already imaged MS data (with the model stored on it), it will self-calibrate
    the data and then perform another imaging iteration. In this imaging it will update the
    threshold to make it 5-times the rms noise level of the residual image.
    """
    # Update these values
    params['gaincal_G']['solint'] = solint
    if os.path.exists("selfcal.{}".format(extname)):
        shutil.rmtree("selfcal.{}".format(extname))

    casa.gaincal(splitdata.msfile, caltable="selfcal.{}".format(extname), calmode=calmode, **params['gaincal_G'])
    casa.applycal(splitdata.msfile, gaintable="selfcal.{}".format(extname), **params['applycal'])

    imagename = splitdata.msfile.replace('.ms', '.{}.{}'.format(params['DEFAULT']['useclean'], extname))
    if params['DEFAULT']['useclean'] == 'tclean':
        cleaning(splitdata, params, imagename)
    elif params['DEFAULT']['useclean'] == 'wsclean':
        wscleaning(splitdata, params, imagename)
    else:
        raise ValueError('Value {} in useclean not known.'.format(params['DEFAULT']['useclean']))


def selfcalibration_loop(msdata, params):
    """Performs the cleaning/self-calibration loop to produce final images on each target source
    from the original SPLIT dataset.
    """
    for a_target in params['DEFAULT']['target']:
        splitfile = "{}.split.ms".format(a_target)
        os.chdir("{}/{}/".format(params['DEFAULT']['outdir'], a_target))
        try:
            splitdata = ms.Ms(splitfile, a_target) # Also checks it exists
            imagename = splitdata.msfile.replace('.ms', '.{}'.format(params['DEFAULT']['useclean']))
            if splitdata.exists:
                # Check the rms in the residuals to update
                for pcycle in range(params['DEFAULT']['pcycles']):
                    # if params['DEFAULT']['useclean'] is 'tclean':
                        # params['tclean']['threshold']
                        # TODO: This needs to be modified!!
                    selfcalibration(splitdata, params, extname="p{}".format(pcycle+1), calmode='p',
                                    solint=params['DEFAULT']['solint'].pop(0))

                flag.flagging(msdata, params, flag_calibrators=False, flag_target=True)
                # Flagging
                for apcycle in range(params['DEFAULT']['apcycles']):
                    selfcalibration(splitdata, params, extname="ap{}".format(pcycle+1), calmode='ap',
                                    solint=params['DEFAULT']['solint'].pop(0))
                # Last pcal cycle
                flag.flagging(msdata, params, flag_calibrators=False, flag_target=True)
                selfcalibration(splitdata, params, extname="p{}".format(pcycle+1), calmode='p',
                                solint=params['DEFAULT']['solint'].pop(0))
            else:
                print('WARNING: {} does not exist. Images not produced.'.format(splitdata.msfile))

        finally:
            os.chdir("../")

