# CAPTURE Pipeline - Direct Execution Mode

## Overview

The CAPTURE pipeline has been refactored to run directly from `main.py` without requiring Snakemake. All pipeline steps now execute sequentially in a single run.

## Changes Made

### 1. Main Pipeline Execution (`src/capture/main.py`)

- **Removed**: Snakemake dependency and workflow orchestration
- **Added**: Direct sequential execution of all pipeline steps
- **Implements**: 11 major pipeline steps that execute based on configuration

### Pipeline Steps Executed:

1. **LTA to FITS Conversion** (if `from_lta = true`)
   - Converts LTA files to FITS format using GMRT tools

2. **FITS to MS Import** (if `from_fits = true`)
   - Imports FITS files into CASA Measurement Set format
   - Creates listobs output for inspection

3. **Initial Flagging** (if `flag_init = true`)
   - Flags first channel
   - Applies quack flagging to scan beginnings/endings

4. **Bad Antenna Detection** (if `find_bad_ants = true`)
   - Identifies problematic antennas (placeholder for full implementation)

5. **Initial Calibration** (if `do_init_cal = true`)
   - Identifies standard calibrators (3C48, 3C147, 3C286, etc.)
   - Performs delay (K) calibration
   - Computes bandpass (B) calibration
   - Performs gain (G) calibration
   - Computes flux scale
   - Applies calibration to all fields

6. **Post-Calibration Flagging** (if `do_flag = true`)
   - Clips outliers in calibrated data

7. **Recalibration** (if `redo_cal = true`)
   - Re-runs calibration after flagging

8. **Split Target Data**
   - Extracts target source data
   - Applies calibration solutions

9. **Data Averaging** (if `chan_avg > 1`)
   - Averages channels to reduce data volume

10. **Dirty Image Creation** (if `make_dirty = true`)
    - Creates dirty (non-cleaned) image of target

11. **Self-Calibration** (if `do_selfcal = true`)
    - Iterative self-calibration loops
    - Phase-only calibration on target
    - Progressive imaging improvements

## New Modules Created

### `src/capture/core/steps.py`
- Defines `PipelineStep` dataclass
- Contains step functions for modular execution
- Provides `PIPELINE_STEPS` dictionary for step management

### `src/capture/utils/pipeline_state.py`
- Manages pipeline execution state
- Tracks completed steps
- Handles file timestamp-based dependency checking
- Allows pipeline resumption after interruption

### Package Initialization Files
- `src/capture/core/__init__.py`
- `src/capture/utils/__init__.py`

## How to Run

### Basic Usage:
```bash
python -m capture.main config_capture.toml
```

### With Working Directory:
```bash
python -m capture.main config_capture.toml --working-dir /path/to/data
```

### With Debug Logging:
```bash
python -m capture.main config_capture.toml --debug
```

### Check Version:
```bash
python -m capture.main --version
```

## Configuration

All pipeline behavior is controlled via the TOML configuration file. Key sections:

- `[input]`: Data sources (LTA, FITS, MS)
- `[output]`: Output file names
- `[flagging]`: Flagging parameters
- `[calibration]`: Calibration settings
- `[imaging]`: Imaging parameters
- `[processing]`: General processing options

## Benefits of This Approach

1. **Simpler Execution**: No need to install or understand Snakemake
2. **Easier Debugging**: Standard Python debugging tools work directly
3. **Better Logging**: Detailed step-by-step logging with timestamps
4. **Sequential Control**: Clear execution order, easier to follow
5. **Error Handling**: Comprehensive try-catch with traceback on debug mode
6. **Resumable**: State management allows resuming interrupted pipelines

## Dependencies

Required Python packages:
- `casatasks`: CASA task interface
- `casatools`: CASA tool interface
- `tomllib`: TOML configuration file parsing (Python 3.11+)

## Notes

- The Snakefile is now **ignored** and not used in execution
- All CASA operations run within the same Python process
- Log files are created with timestamps: `capture_HH_MM_SS_DD_MM_YYYY.log`
- Pipeline state is saved to `.capture_state.json` (optional feature)

## Migration from Snakemake

If you were previously using Snakemake:
- Remove any Snakemake-specific commands
- Use the new `python -m capture.main` command instead
- Configuration files remain the same (no changes needed)
- All outputs will be in the same locations as before
