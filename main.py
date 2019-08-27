import os
import sys
# import glob
import shutil
import ConfigParser
import logging
# import datetime
from collections import defaultdict#, namedtuple
import numpy as np
from casa import *

from functions import ms







# Import required? (from LTA, FITS)


# Create the original MS
ms.MS() # to include as parameter the path to MS


# Create the basic structure of folders where the output of
# the pipeline will be created.


# I would need to process the spw syntax if given as a float!






################ OLD STUF #################################
__file__ = '/jop93_0/Programing/gmrt_pipeline'
# os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Little patch for now
sys.path.append(__file__)

# import plotting as pl


_pipeline_dir = os.path.dirname(__file__+'/main.py')
_default_input_file = _pipeline_dir +  '/default_inputs.inp'

input_file = sys.argv[-1]


# Checks that both, the default one and the input one exists
if not os.path.isfile(_default_input_file):
    # logger.exception('Default input file not found (expected at {})'.format(_default_input_file))
    raise IOError('File {} not found.'.format(_default_input_file))

if not os.path.isfile(input_file):
    # logger.exception('Input file {} not found.'.format(input_file))
    raise IOError('File {} not found.'.format(input_file))

config = ConfigParser.ConfigParser()
# Read the file with all the default parameters to use in the pipeline
config.read(_default_input_file)
# Upload the parameters with the inputs from the user (the provided file)
config.read(input_file)

parameters = defaultdict(dict)

# Interpret all parameters to their correct type (integers, booleans, str, lists)
# DEFAULT section appears independently
for a_param in config.defaults():
    parameters['DEFAULT'][a_param] = uf.evaluate(config.defaults()[a_param])

for a_section in config.sections():
    for a_param in config.options(a_section):
        # Only those ones that are not in DEFAULTS
        if a_param not in parameters['DEFAULT']:
            parameters[a_section][a_param] = uf.evaluate(config.get(a_section, a_param))


######### Let's create the logger
logger = logging.getLogger(__name__)
logger_stdout = logging.StreamHandler(stream=sys.stdout)
logger_errlog = logging.FileHandler(filename=parameters['DEFAULT']['outdir']+'/'+parameters['DEFAULT']['logger'])

# Formatters TODO
# logger_formatter = logging.Formatter('%(levelname)s: %(name)s  -  %(message)s')
# logger_stdout.setFormatter(logger_formatter)
# logger_errlog.setFormatter(logger_formatter)

logger.addHandler(logger_errlog)
logger.addHandler(logger_stdout)

logger.setLevel('DEBUG')
logger_errlog.setLevel('DEBUG')
logger_stdout.setLevel('DEBUG')


###################### Starting the pipeline

times = [] # Will keep an ordered sample of times
times.append(datetime.datetime.now())

logger.info('EVN CASA Pipeline starting at {}'.format(times[-1]))


# Pre-processing steps are required. See CASA tutorial (gc.py, antabs..)


# steps can be just an integer or also a couple of integers (first, and last step to execute)
if type(parameters['DEFAULT']['steps']) == int:
    parameters['DEFAULT']['steps'] = (parameters['DEFAULT']['steps'], 999)

assert parameters['DEFAULT']['steps'][0] <= parameters['DEFAULT']['steps'][1]

logger.info('Pipeline to execute steps (steps) from {} to {}'.format(parameters['DEFAULT']['steps'][0],
                                                                      parameters['DEFAULT']['steps'][1]))



# Check that all directories exist  os.path.isdir
# for a_dir_name in ('outdir'):
#     # Removes the trailing / if it is present in all directories path
#     if parameters['DEFAULT'][a_dir_name].strip()[-1] == '/':
#         parameters['DEFAULT'][a_dir_name] = parameters['DEFAULT'][a_dir_name].strip()[:-1]
#
#     if not os.path.isdir(parameters['DEFAULT'][a_dir_name]):
#         if parameters['DEFAULT']['create_new_directories']:
#             os.makedirs(parameters['DEFAULT'][a_dir_name])
#
#         else:
#             raise FileNotFoundError('No such file or directory: {}'.format(a_dir))

# Make sure all inputs related to sources are lists (even if only one source specified)
if type(parameters['DEFAULT']['bpass']) is not list:
    parameters['DEFAULT']['bpass'] = [ parameters['DEFAULT']['bpass'] ]

if parameters['DEFAULT']['phaseref'] is not None:
    if type(parameters['DEFAULT']['phaseref']) is not list:
        parameters['DEFAULT']['phaseref'] = [ parameters['DEFAULT']['phaseref'] ]

    if type(parameters['DEFAULT']['target']) is not list:
        parameters['DEFAULT']['target'] = [ parameters['DEFAULT']['target'] ]

    assert len(parameters['DEFAULT']['phaseref']) == len(parameters['DEFAULT']['target'])


# Check if this is a phase-referencing experiment
if parameters['DEFAULT']['phaseref'] is not None:
    if len(parameters['DEFAULT']['phaseref']) != len(parameters['DEFAULT']['target']):
        logger.exception('The parameters phaseref and target must contain the same number of source.')
        print(parameters['DEFAULT']['phaseref'])
        print(parameters['DEFAULT']['target'])
        raise NameError('phaseref ({}) and target ({}) must contain the same number of sources'.format(
            len(parameters['DEFAULT']['phaseref']), len(parameters['DEFAULT']['target'])))

msinfo = uf.get_info_from_ms(parameters['DEFAULT']['msfile'])

# Updating all the sources to consider (either specified in sources, or accounting for bpass/phaseref/target
# Just wait to see following lines, I will only leave the good ones.
if parameters['DEFAULT']['sources'] == None:
    # msinfo['calibrators'] = msinfo['sources'].copy() # Not available in Python 2.7...
    msinfo['calibrators'] = list(msinfo['sources'])
else:
    # msinfo['sources'] = [i.strip() for i in parameters['DEFAULT']['sources'].split(',')]
    msinfo['sources'] = parameters['DEFAULT']['sources']
    msinfo['calibrators'] = list(parameters['DEFAULT']['sources'])

# Remove the targets from the calibrators (calibrators defined as sources to use in fringe)
if parameters['DEFAULT']['phaseref'] is not None:
    for a_target in parameters['DEFAULT']['target']:
        msinfo['calibrators'].remove(a_target)



files = uf.build_required_names(parameters['DEFAULT'], msinfo)





################ Inspecting the data

if parameters['DEFAULT']['steps'][0] <= 1 <= parameters['DEFAULT']['steps'][1]:
    uf.print_log_header(logger, 'Inspecting the data')
    times.append(datetime.datetime.now())
    logger.info('Starting at {}'.format(times[-1]))
    logger.info('Running listobs...')
    listobs(vis=files['msfile'], listfile=parameters['DEFAULT']['outdir']+parameters['DEFAULT']['codename']+'.SCAN',
            overwrite=True)
    if parameters['DEFAULT']['doplot']:
        logger.info('Running plotants...')
        plotants(vis=files['msfile'], figfile=parameters['DEFAULT']['outdir']+'.plotants.pdf')
        for a_source in paramters['DEFAULT']['sources']:
            logger.info('Running plotuv...')
            plotuv(vis=msfiles['msfile'], field=a_source, figfile=parameters['DEFAULT']['outdir']+'_'+a_source+'.uv.pdf')

    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))


################ flagging
if parameters['DEFAULT']['steps'][0] <= 2 <= parameters['DEFAULT']['steps'][1]:
    uf.print_log_header(logger, 'Flagging')
    if parameters['flagging']['doclip']:
        for a_bpass in parameters['DEFAULT']['bpass']:
            flagdata(vis=files['msfile'], field=a_bpass, datacolumn='DATA',  **parameters['flag_clip'])
        for a_phaseref in parameters['DEFAULT']['phaseref']:
            flagdata(vis=files['msfile'], field=a_phaseref, datacolumn='DATA', **parameters['flag_clip'])

    for a_calibrator in msinfo['calibrators']:
        if parameters['flagging']['dotfcrop']:
            flagdata(vis=files['msfile'], field=a_calibrator, datacolumn='DATA', **parameters['flag_tfcrop'])

        if parameters['flagging']['dorflag']:
            flagdata(vis=files['msfile'], field=a_calibrator, datacolumn='DATA', **parameters['flag_rflag'])

        if parameters['flagging']['doextend']:
            flagdata(vis=files['msfile'], field=a_calibrator, datacolumn='DATA', **parameters['flag_extend'])

        if parameters['flagging']['doaoflagger']:
            logger.warning('WARNING: AOFlagger not implemented yet. This step is going to be ignored.')

    # Do a summary of all flagging
    flagdata(vis=files['msfile'], mode='summary', datacolumn='DATA', extendflags=True, overwrite=True, writeflags=True,
            name=parameters['DEFAULT']['outdir']+'/flagging-summary.log', action='apply', flagbackup=True)

    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))



################ Plotting uncalibrated data
if parameters['DEFAULT']['steps'][0] <= 3 <= parameters['DEFAULT']['steps'][1]:
    uf.print_log_header(logger, 'Plotting uncalibrated data')
    if parameters['DEFAULT']['doplot']:
        # plotms(msfiles['msdata'], gridrows=3, gridcols=3, xaxis='spw', yaxis='amp', ydatacolumn='data',
        #        field=','.join(parameters['DEFAULT']['bpass']), correlation='rr,ll', avgscan=True,
        #        iteraxis='scan,antenna,corr', showlegend=True, plotfile=plotfiles['uncal']['autocorr'],
        #        exprange='all', dpi=300, overwrite=True, showgui=False, clearplots=True)
        logger.warning('Plotting uncalibrated data not implemented yet.')

    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))


################ Generate a-priori calibration tables (Tsys and gain curve).
if parameters['DEFAULT']['steps'][0] <= 4 <= parameters['DEFAULT']['steps'][1]:
    uf.print_log_header(logger, 'Calibration')
    # Remove the calibration previous if they already exist
    if os.path.exists(files['cal']['gain_K']):
        shutil.rmtree(files['cal']['gain_K'])

    if os.path.exists(files['cal']['bpass']):
        shutil.rmtree(files['cal']['bpass'])

    if os.path.exists(files['cal']['gain_G']):
        shutil.rmtree(files['cal']['gain_G'])

    if os.path.exists(files['cal']['fluxscale']):
        shutil.rmtree(files['cal']['fluxscale'])

    setjy(vis=files['msfile'], field=','.join(parameters['DEFAULT']['bpass']), **parameters['setjy'])

    gaincal(vis=files['msfile'], caltable=files['cal']['gain_K'], field=','.join(parameters['DEFAULT']['bpass']),
            **parameters['gaincal_K'])

    bandpass(vis=files['msfile'], caltable=files['cal']['bpass'], field=','.join(parameters['DEFAULT']['bpass']),
            **parameters['bpass'])

    gaincal(vis=files['msfile'], caltable=files['cal']['gain_G'], field=','.join(msinfo['calibrators']), calmode='ap',
            gaintable=[files['cal']['gain_K'], files['cal']['bpass']], **parameters['gaincal_G'])

    fluxscale(vis=files['msfile'], caltable=files['cal']['gain_G'], reference=','.join(parameters['DEFAULT']['bpass']),
              transfer=','.join(parameters['DEFAULT']['phaseref']), fluxtable=files['cal']['fluxscale'],
              **parameters['fluxscale'])

    for a_bpass in parameters['DEFAULT']['bpass']:
        applycal(vis=files['msfile'], field=a_bpass, gaintable=[files['cal']['gain_K'],
                 files['cal']['bpass'], files['cal']['fluxscale']], gainfield=[a_bpass, a_bpass, a_bpass],
                 **parameters['applycal'])

    for a_phaseref, a_target in zip(parameters['DEFAULT']['phaseref'], parameters['DEFAULT']['target']):
        applycal(vis=files['msfile'], field=a_phaseref, gaintable=[files['cal']['gain_K'], files['cal']['bpass'],
                 files['cal']['fluxscale']], gainfield=[','.join(parameters['DEFAULT']['bpass']),
                 ','.join(parameters['DEFAULT']['bpass']), a_phaseref], **parameters['applycal'])

        applycal(vis=files['msfile'], field=a_target, gaintable=[files['cal']['gain_K'], files['cal']['bpass'],
                 files['cal']['fluxscale']], gainfield=[','.join(parameters['DEFAULT']['bpass']),
                 ','.join(parameters['DEFAULT']['bpass']), a_phaseref], **parameters['applycal'])


    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))



############### Plotting calibrated data

if parameters['DEFAULT']['steps'][0] <= 5 <= parameters['DEFAULT']['steps'][1]:
    if parameters['DEFAULT']['doplot']:
        pass



################ Split files

if parameters['DEFAULT']['steps'][0] <= 6 <= parameters['DEFAULT']['steps'][1]:
    for a_source in msinfo['sources']:
        uf.print_log_header(logger, 'Removing existing split files')
        if os.path.exists(files[a_source]['split']):
            shutil.rmtree(files[a_source]['split'])

        uf.print_log_header(logger, 'Creating split files for {}'.format(a_source))
        split(vis=files['msfile'], outputvis=files[a_source]['split'], field=a_source, **parameters['split'])

    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))


################ Flagging target split data

if parameters['DEFAULT']['steps'][0] <= 7 <= parameters['DEFAULT']['steps'][1]:
    for a_target in parameters['DEFAULT']['target']:
        uf.print_log_header(logger, 'Flagging')
        if parameters['flagging']['doclip']:
            flagdata(vis=files[a_target]['split'], datacolumn='DATA', **parameters['flag_clip'])
            flagdata(vis=files[a_target]['split'], datacolumn='DATA', **parameters['flag_clip'])

        if parameters['flagging']['dotfcrop']:
            flagdata(vis=files[a_target]['split'], datacolumn='DATA', **parameters['flag_tfcrop'])

        if parameters['flagging']['dorflag']:
            flagdata(vis=files[a_target]['split'], datacolumn='DATA', **parameters['flag_rflag'])

        if parameters['flagging']['doextend']:
            flagdata(vis=files[a_target]['split'], datacolumn='DATA', **parameters['flag_extend'])

        if parameters['flagging']['doaoflagger']:
            logger.warning('WARNING: AOFlagger not implemented yet. This step is going to be ignored.')

        # Do a summary of all flagging
        flagdata(vis=files[a_target]['split'], datacolumn='DATA', extendflags=True,
                 name=parameters['DEFAULT']['outdir']+'/flagging-summary-'+a_target+'.log', action='apply',
                 flagbackup=True, overwrite=True, writeflags=True)

    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))




################ Create clean maps

if parameters['DEFAULT']['steps'][0] <= 8 <= parameters['DEFAULT']['steps'][1]:
    # temp_niter = parameters['clean'].pop('niter')
    # Getting the optimal cellsize depending on the robust
    # if parameters['tclean']['weighting'] == 'natural':
    #     cellsize = str(msinfo['resolution']/10.)+'arcsec'
    # elif parameters['tclean']['weighting'] == 'uniform':
    #     cellsize = str(msinfo['resolution']/40.)+'arcsec'
    # else:
    #     cellsize = '{:4f}arcsec'.format(msinfo['resolution']/(-30/4.*parameters['tclean']['robust']+25))

    # Create initial images of the phasecalibrators
    # for a_source in msinfo['sources']:
    for a_source in parameters['DEFAULT']['target']:
        if os.path.exists(files[a_source]['split']+'.clean*'):
            uf.print_log_header(logger, 'Removing existing image files for {}'.format(a_source))
            shutil.rmtree(files[a_source]['split']+'.clean*')

        uf.print_log_header(logger, 'Creating image files for {}'.format(a_source))
        tclean(vis=files[a_source]['split'], imagename=files[a_source]['split']+'.clean', field=a_source,
                **parameters['tclean'])

    times.append(datetime.datetime.now())
    logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))


################ Selfcalibrate targets

if parameters['DEFAULT']['steps'][0] <= 9 <= parameters['DEFAULT']['steps'][1]:
    for a_target in parameters['DEFAULT']['target']:
        # Number of loops with phase-only self-calibration
        logger.info('Self calibrating target source {} for the cycle no. {}'.format(a_target, pcycle))
        logger.info('Flaggin target source {} for the cycle no. {}'.format(a_target, pcycle))

        if parameters['flagging']['doclip']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])

        if parameters['flagging']['dorflag']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_rflag'])

        if parameters['flagging']['doaoflagger']:
            logger.warning('WARNING: AOFlagger not implemented yet. This step is going to be ignored.')

        for pcycle in range(parameters['DEFAULT']['pcycles']):
            parameters['gaincal_g'].pop('solint')
            gaincal(vis=files[a_target]['split'],
                    solint='{:.2}min'.format(parameters['DEFAULT']['solint']/(pcycle+1)),
                    calmode='p', caltable=files['cal']['psc{}'.format(pcycle)], **parameters['gaincal_G'])
            applycal(vis=files[a_target]['split'], gaintable=files['cal']['psc{}'.format(pcycle)],
                     applymode='calflag', **parameters['applycal'])
            tclean(vis=files[a_target]['split'], imagename=files[a_target]['split']+'.clean.p{}'.format(pcycle),
                   field=a_target, **parameters['tclean'])

        # Doing a final flagging before AP selfcal
        if parameters['flagging']['doclip']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])

        if parameters['flagging']['dorflag']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_rflag'])

        if parameters['flagging']['doaoflagger']:
            logger.warning('WARNING: AOFlagger not implemented yet. This step is going to be ignored.')

        for apcycle in range(parameters['DEFAULT']['apcycles']):
            gaincal(vis=files[a_target]['split'], solint='{:.2}min'.format(200/(pcycle+1)),
                    calmode='ap', caltable=files['cal']['apsc{}'.format(pcycle)], **parameters['gaincal_G'])
            applycal(vis=files[a_target]['split'], gaintable=files['cal']['apsc{}'.format(pcycle)],
                     applymode='calflag', **parameters['applycal'])
            tclean(vis=files[a_target]['split'], imagename=files[a_target]['split']+'.clean.ap{}'.format(apcycle),
                   field=a_target, **parameters['tclean'])

        # Doing a final flagging before final selfcal
        if parameters['flagging']['doclip']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_clip'])

        if parameters['flagging']['dorflag']:
            flagdata(vis=files[a_target]['split'], datacolumn='RESIDUAL', **parameters['flag_rflag'])

        if parameters['flagging']['doaoflagger']:
            logger.warning('WARNING: AOFlagger not implemented yet. This step is going to be ignored.')

        gaincal(vis=files[a_target]['split'], solint='{:.2}min'.format(parameters['DEFAULT']['solint']),
                calmode='p', caltable=files['cal']['final'], **parameters['gaincal_G'])
        applycal(vis=files[a_target]['split'], gaintable=files['cal']['final'],
                 applymode='calflag', **parameters['applycal'])
        tclean(vis=files[a_target]['split'], imagename=files[a_target]['split']+'.clean.final',
               field=a_target, **parameters['tclean'])

        times.append(datetime.datetime.now())
        logger.info('Finishing at {}. It took {} s.'.format(times[-1], (times[-1]-times[-2]).total_seconds()))


logger.info('The pipeline finished happily after {:.2f} min.'.format((times[-1]-times[0]).total_seconds()/60.))

