
from collections import defaultdict
import numpy as np
from casac import casac


# Flagging functions

# NOT NEEDED ANY MORE

def flagging(mode='casa', **kwargs):
    """Run a typical flagging process on the data.
    Two modes are supported:
      - casa : run the flagdata command from CASA
      - aoflagger : run the flagging program AOFlagger
    Options required for each of the mode can be parsed in as additional parameters.
    """
    if mode == 'casa':
        flagging_casa(**kwargs)
    elif mode == 'aoflagger':
        flagging_aoflagger(**kwargs)
    else:
        raise ValueError('The specified mode ({}) is not supported'.format(mode))


def flagging_aoflagger(**kwargs):
    """Perform a flagging on the data by running AOFlagger
    """
    raise NotImplemented


def flagging_casa(**kwargs):
    """Runs flagdata with all provided commands.
    """


# NOTE I may need to modify eval if for lists (with []) it does not recognize if there are
# strings without quote marks explicitily set

def evaluate(entry):
    """Evaluate the type of the string entry and convert it to its expected one.
    e.g. entry is a string containing a float. This function would return a float
    with that value (equivalent to eval(entry)).
    The enhancement is that eval_param_type can also evaluate if a list is present
    (eval does not work if no brackets are literally written, as in 1, 2, 3.)

    Useful function to evaluate all values stores by the ConfigParser (as it assumes
    that everything is a strings.
    """
    # If it is a tentative list
    if ',' in entry:
        if ('[' in entry) and (']' in entry):
            # If has brackets, eval works fine. NO, this sentence was a lie
            #return eval(entry)
            entry = entry.replace('[', '')
            entry = entry.replace(']', '')
            try:
                return [eval(i) for i in entry.split(',')]

            except NameError:
                # it would fail if i is a str.
                return [i.strip() for i in entry.split(',')]

        elif ('[' not in entry) == (']' in entry):
            # If only one is there, something is wrong
            raise ValueError('Format of {} unclear.'.format(entry))

        else:
            # it is a list without brackets
            try:
                return [eval(i.strip()) for i in entry.split(',')]

            except NameError:
                # it would fail if i is a str.
                return [i.strip() for i in entry.split(',')]

    else:
        return eval(entry)



def build_required_names(inputs, msinfo):
    """Returns a dictionary with all the files that are going to be created within the
    pipeline. That is:
        - msdata : file with all the raw uvdata (and/or calibration applied).
        Per each specified source (in bpass, phaseref, target, sources
            - uvdata : for the calibrated uvdata
            - dirty  : dirty image of the source
            - clean  : clean image of the source
            - selfcal{i} : i-iteraction of selfcalibrated image of the source.
    """
    files = defaultdict(dict)
    # files['msdata'] = '{}/{}.{}'.format(inputs['outdir'], inputs['codename'], extension)
    files['msfile'] = inputs['msfile']

    # SPLIT files per source
    for a_source in msinfo['sources']:
        files[a_source]['split'] = '{}/{}.{}.ms'.format(inputs['outdir'], inputs['codename'], a_source)
        for pcycle in range(inputs['pcycles']):
            files[a_source]['asc{}'.format(pcycle)] = '{}/{}.{}.asc{}.ms'.format(inputs['outdir'],
                    inputs['codename'], a_source, pcycle)
        for apcycle in range(inputs['apcycles']):
            files[a_source]['apsc{}'.format(pcycle)] = '{}/{}.{}.apsc{}.ms'.format(inputs['outdir'],
                    inputs['codename'], a_source, apcycle)

        files[a_source]['final'] = '{}/{}.{}.final.ms'.format(inputs['outdir'], inputs['codename'], a_source)

    # CAL tables
    for a_key, a_file in zip(('gain_K', 'gain_G', 'bpass', 'fluxscale'), ('cal.K', 'cal.G', 'cal.bp', 'cal.fx')):
        files['cal'][a_key] = a_file

    for i in range(inputs['pcycles']):
        files['cal']['psc{}'.format(i)] = 'cal.sc.p{}'.format(i)

    for i in range(inputs['apcycles']):
        files['cal']['apsc{}'.format(i)] = 'cal.sc.ap{}'.format(i)

    return files



def print_log_header(logger, title):
    """Prints a entry in the logging formatted as a heading with title.
    """
    s = '#'*80 + '\n'
    s += '###  '+title+'\n'
    s += '#'*80 + '\n'
    logger.info(s)



def get_info_from_ms(msfile):
    """Returns a dictionary with useful information from the observations in the MS,
    as the number of channels, number of subbands, rest frequency, integration time,
    max. baseline and max. resolution of the data.
    """
    msinfo = {}
    ms = casac.ms()
    ms.open(msfile)
    msinfo['channels'] = ms.metadata().nchan(0) #ms.getspectralwindowinfo()['0']['NumChan']
    msinfo['subbands'] = ms.metadata().nspw() #len(ms.getspectralwindowinfo())
    # CHECK SPEED WITH ONE METHOD AND THE OTHER
    # msinfo['subbands'] = len(vishead(msfiles['msdata'], mode='get', hdkey='spw_name')[0])
    msinfo['reffreq'] = 5e9#ms.getspectralwindowinfo()[str(msinfo['subbands']//2)]['RefFreq'] # In Hz
    keys = ms.getscansummary().keys()
    a_key = 1
    while str(a_key) not in keys:
        a_key += 1

    msinfo['inttime'] = ms.getscansummary()[str(a_key)]['0']['IntegrationTime']
    del a_key

    # Getting the longest baseline
    msinfo['max_baseline'] = 30000 #au.getBaselineExtrema(msfiles['msdata'])[0] # In meters
    msinfo['resolution'] = (2.44*(3e8/msinfo['reffreq'])/msinfo['max_baseline'])*180*3600/np.pi # in arcsec
    msinfo['sources'] = ms.metadata().fieldnames()
    ms.done()
    return msinfo




