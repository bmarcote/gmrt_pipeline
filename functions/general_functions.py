
from collections import defaultdict
import numpy as np
from casac import casac


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


def build_folder_structure(path):
    """Builds the full directory structure that is expected for the pipeline.
    """
    pass

# This should be completely changed
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




