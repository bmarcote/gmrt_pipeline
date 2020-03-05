# -*- coding: utf-8 -*-

# General functions required by the pipeline operations.
#
# @Author: Benito Marcote
# @Email: marcote@jive.eu

import os
import casa_functions as cf
import flagging as flag


class Steps(object):
    """Contains the steps that can be run within CAGA.
    It contains the full list of all steps, but it provides the steps that
    are requested to be run from the init file (plus some (user-hidden) functions
    that may be required by the code to run properly but are transparent to the
    users).
    """
    # NOTE: for Python 3.6 the dict will preserve order... not for current CASA
    # This is just a workaround due to that.
    def __init__(self):
        self._step_functions = {'inspect': [cf.data_inspection],
                        'get_caltables': [cf.get_existing_caltables],
                        # 'initial_flagging': [flag.bad_antennas, flag.cal_flagging],
                        'initial_flagging': [flag.cal_flagging],
                        # TODO: ionospheric calibration fails reporting: Error in Calibarter::specifycal.
                        # No idea why... Just following values for VLA?
                        # 'calibration': [cf.ionospheric_calibration, cf.initial_calibration],
                        'calibration': [cf.initial_calibration],
                        'bandpass': [cf.bandpass_calibration],
                        'calibration': [cf.second_calibration],
                        'fluxscale': [cf.fluxscale_calibration],
                        'applycal': [cf.apply_calibration],
                        'postcal_flagging': [flag.target_flagging],
                        'split': [cf.split_sources],
                        'clean': [cf.imaging],
                        'selfcal': [cf.selfcalibration_loop],
                        }

    @property
    def step_functions(self):
        return self._step_functions

    def get_step_function(self, step):
        return self._step_functions[step]

    @property
    def all_steps(self):
        """Dictionary with all steps that
        """
        return ('inspect', 'get_caltables', 'initial_flagging', 'calibration', 'bandpass'
            'calibration', 'fluxscale', 'applycal', 'postcal_flagging', 'split', 'clean', 'selfcal')
        # TODO: steps to add in the future: phasecal_clean/selfcal?  ltaimport, fitsimport

    @property
    def mandatory_steps(self):
        """Steps that will be executed in every single CAGA run (even if not specified
        in the input file, as they are required for the correctly working of the code.
        """
        return ('get_caltables')

    def steps_to_perform(self, input_steps_list):
        """Returns the functions that will be executed in the pipeline by considering both
        the steps to execute as input from the user plus the mandatory functions required
        by the pipeline.
        """
        stepfunctions = []
        for a_step in self.all_steps:
            if (a_step in input_steps_list) or (a_step in self.mandatory_steps):
                for a_function in self.step_functions[a_step]:
                    stepfunctions.append(a_function)

        return stepfunctions




def create_directory_tree(params):
    # Create the basic structure of folders where the output of
    # the pipeline will be created.
    dir_tree = ('log', 'plots', 'caltables')
    for a_subdir in dir_tree:
        if not os.path.exists("{}/{}".format(params['DEFAULT']['outdir'], a_subdir)):
            os.makedirs("{}/{}".format(params['DEFAULT']['outdir'], a_subdir))




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
                return [eval(i) for i in entry.split(',')]

            except NameError:
                # it would fail if i is a str.
                return [i.strip() for i in entry.split(',')]

    elif entry == '.':
        return '.'
    else:
        if len(entry) == 0:
            return entry

        if entry[0] == "'" and entry[-1] == "'":
            return str(entry[1:-1])

        return eval(entry)


