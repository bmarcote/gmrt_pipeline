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





## Structure of CAGA

- `main.py`: The main script that is executed when the Pipeline is launched in CASA.
- `template.inp`: Template of an input file. Copy to your working directory before running CAGA.
- `functions/`
    -  *Different flagging functions.*
    -  *Different calibration functions.*
    -  *Different plotting functions.*
- `classes/`
    - `ms.py`: Defines a MS class that would directly include all necessary information CAGA needs.
    - `sources.py`: Defines all sources that will be considered in the analysis and the intent of each of them.


## Random ideas

Forget about tmask, write a parameter that is a list of all tasks to conduct. Same as in NDPPP.


