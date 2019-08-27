# GAPA - uGMRT CASA Pipeline Analysis
# CAGA - CASA Analysis of GMRT datA


Pipeline to analyze data from the Giant Metrewavelength Radio Telescope (GMRT). It is particularly focused on the analysis of data from the new backend (upgraded-GMRT or uGMRT).



<!-- ## Acknowledgements -->

This code is partially based on the pipelines developed independently by Ruta (PUT LINK) and Ishwara Chandra. It also gets the structure inspiration from the EVN Pipeline (ADD LINK).


##  Motivation for CAGA

Most of the procedures in GMRT data reduction can be easily automatized and the size of the new datasets makes a manual calibration nearly unfeasible. The current packages provide accurate enough procedures to allow astronomers an almost-automatic data reduction. CAGA is intended to perform this reduction that will work in most of the cases with limited manual interaction.


### Input files

Only an input file (see `template.inp` for an example) is the only file that should be configured and loaded into the pipeline to run the full process. It must contain all necessary data like the input data files, all steps to conduct, and the output files to produce.
CAGA can then run by executing:

```bash
casa -c CAGA.py -i template.inp
```

This input file can override any parameter used in any CASA task, providing full flexibility to the user. However, if not specified, CAGA would assume the default parameters that are (at the current moment) thought to optimize GMRT data reduction.


## Files and folders that will be created in the working directory

When CAGA runs, it will create several files and directories. Whereas the final number fo files created depends on the steps specified in the input file, the general idea is that the following directories will appear:
- `plots/`: Plots generated from different stages of the calibration that give you a good idea on how the calibration has performed.
- `images/`: Images of the sources that have been analyzed. It will contain both FITS and pdf files.
- `splits/`: The calibrated single-source data in MS.
- `calibration/`: calibration tables generated during the data reduction.
- `log/`: The different log and txt files produced from the output of the different procedures.



## Structure of CAGA

- `main.py`: The main script that is executed when the Pipeline is launched in CASA.
- `template.inp`: Template of an input file. Copy to your working directory before running CAGA.
- `functions/`
    - `general_functions.py`.
    - `plotting_functions.py`
    - `flagging_functions.py`
    -  *Different calibration functions.*
- `classes/`
    - `ms.py`: Defines a MS class that would directly include all necessary information CAGA needs.
    - `sources.py`: Defines all sources that will be considered in the analysis and the intent of each of them.


## Calibration steps performed in CAGA

The user can specify all steps that wish to perform via the input file. Here we specify the standard ones that are typically conducted in a GMRT data reduction and thus are performed by default.

- Import data [IF NEEDED]
    - From lta files.
    - From FITS files.
- Inspecting the data
    - Create a listobs.txt file with the output of `listobs()` from CASA.
    - Produce the plot of the array configuration.
    - Produce plots of the raw data from the amplitude calibrators.
- Plotting the raw data (jplotter)




## Random ideas

- Forget about tmask, write a parameter that is a list of all tasks to conduct. Same as in NDPPP.
- Add a first step to be able to run from lta files.

