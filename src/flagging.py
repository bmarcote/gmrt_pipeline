import sys
import subprocess
import numpy as np
import casa

def bad_antennas(msdata, params):
    """Finds the antennas that did not record properly during the observation.
    To find it, computes the mean amplitudes for the given fields (ideally only
    calibrator scans). If these amplitudes are lower than the provided amp_cutoff,
    the station is marked as bad antenna.

    Parameters:
        msfile : str
            The MS file to evaluate.
        field : str
            The fields used to evaluate the amplitudes (should only include calibrator
            sources).
        spw : str
            The spw used to evaluate the amplitudes.
        amp_cutoff : float [DEFAULT = 0.4]
            The amplitude cutoff to interpretate an antenna as bad one.

    Returns:
        bad_antennas : list
            A list with the name of the antennas showing bad data.
    """
    print('WARNING: Flagging.bad_antennas has not been implemented yet.')
    raise NotImplemented('Flagging.bad_antennas has not been implemented yet.')
    # thevalues = np.zeros((len(msfile.antennas), msfile.num_corr))
    # for an_antenna in msfile.antennas:
    #     for a_corr in range(msfile.num_corr+1):
    #         a_stokes = generic.stokes(a_corr)
    # thestats = casa.visstat(msfile, field=field, spw=spw, antenna=an_antenna, correlation=a_corr, axis='amp',
    #                     datacolumn='data', useflags=False, selectdata=True, uvrange="", maxuvwdistance=0.0,
    #                     timerange="", timeaverage=False, timebin="0s", timespan="", disableparallel=None,
    #                     ddistart=None, taql=None, monolithic_processing=None, intent="", reportingaxes="ddid")



def clip_highamp(msdata, params):
    """Clips visibilities with very high amplitudes.
    """
    for a_source in msdata.sources:
        casa.flagdata(vis=msdata.msfile, field=a_source, **params['flag_clip'])


def flag_zerochannel(msdata, params):
    """Flags the zero channel for all IFs.
    """
    casa.flagdata(vis=msdata.msfile, **params['flag_zerochan'])


def quack(msdata, params):
    """Performs a quack flaggging. quackmode and cmdreason can be a list with different
    options.
    """
    if 'quackmode' in params['flag_quack']:
        casa.flagdata(vis=msdata.msfile, **params['flag_quack'])
    else:
        casa.flagdata(vis=msdata.msfile, quackmode='beg', **params['flag_quack'])
        casa.flagdata(vis=msdata.msfile, quackmode='endb', **params['flag_quack'])


def flag_badchannels(msdata, params):
    """Flags channels that contain known persistent RFI
    """
    rfifreqall = params['flag_badchan']['rfifreqs']
    raise NotImplemented('flag_badchannels has not been fully implemented yet.')


def cal_flagging(msdata, params):
    """Performs an exhaustive CASA flagging on the data, but only on calibrators
    (target data will not be flagged).
    """
    flagging(msdata, params, flag_calibrators=True, flag_target=False)


def target_flagging(msdata, params):
    """Performs an exhaustive CASA flagging on the data, only on the target sources.
    """
    flagging(msdata, params, flag_calibrators=False, flag_target=True)


def full_flagging(msdata, params):
    """Performs an exhaustive CASA flagging on the data, on all available sources.
    """
    flagging(msdata, params, flag_calibrators=True, flag_target=True)


def flagging(msdata, params, flag_calibrators=True, flag_target=False):
    """Performs an exhaustive CASA flagging on the data.
    flag_target defines if the targe-source data should be considered to perform the flagging or not.
    """
    source_list = []

    if flag_calibrators:
        source_list += params['DEFAULT']['ampcalibrator']
        if params['DEFAULT']['phaseref'] is not None:
            source_list += params['DEFAULT']['phaseref']

    if flag_target:
        source_list += params['DEFAULT']['target']

    # For consistence, as msdata could be a SPLIT/SPLAT file that does not contain all sources.
    source_list = [a_source for a_source in source_list if a_source in msdata.sources]
    for a_source in source_list:
        if params['flagging']['doclip']:
            clip_highamp(msdata, params)

        if params['flagging']['dozerochan']:
            flag_zerochannel(msdata, params)

        if params['flagging']['dobadchan']:
            flag_badchannels(msdata, params)

        if params['flagging']['doquack']:
            quack(msdata, params)

        if params['flagging']['dotfcrop']:
            casa.flagdata(vis=msdata.msfile, field=a_source, datacolumn='DATA', **params['flag_tfcrop'])

        if params['flagging']['dorflag']:
            casa.flagdata(msdata.msfile, field=a_source, datacolumn='DATA', **params['flag_rflag'])

        if params['flagging']['doextend']:
            casa.flagdata(msdata.msfile, field=a_source, datacolumn='DATA', **params['flag_extend'])

        if params['flagging']['doaoflagger']:
            # try:
            print('Running AOFlagger')
            proc = subprocess.Popen('aoflagger -strategy {} {}'.format(params['flag_aoflagger']['rfi_strategy'],
                          msdata.msfile), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while proc.poll() is None:
                out = proc.stdout.read().decode('utf-8')
                sys.stdout.write(out)
                sys.stdout.flush()

            # print('Opening AOFlagger log file')
            # with open(params['flag_aoflagger']['output_log'], 'a') as aoflagger_logfile:
            #     print('AOFlagger log file openned')
            #     while proc.poll() is None:
            #         out = proc.stdout.read(1).decode('utf-8')
            #         sys.stdout.write(out)
            #         aoflagger_logfile.write(out)
            #         sys.stdout.flush()

            # except Exception as e:
            #     raise NotImplemented('AOflagger flagging is not implemented yet or not found. Error: {}'.format(e))

    # Do a summary of all flagging
    casa.flagdata(vis=msdata.msfile, mode='summary', datacolumn='DATA', extendflags=True, overwrite=True,
            writeflags=True, name=params['flagging']['summary_outputfile'], action='apply', flagbackup=True)



