# CAPTURE Pipeline - Quick Start Guide

## Running the Pipeline

The CAPTURE pipeline now runs directly from `main.py` without requiring Snakemake.

### Basic Command

```bash
python -m capture.main config_capture.toml
```

### With Options

```bash
# Run in a specific directory
python -m capture.main config_capture.toml --working-dir /path/to/data

# Enable debug mode for detailed logging
python -m capture.main config_capture.toml --debug

# Check version
python -m capture.main --version
```

## Configuration File

Edit `config_capture.toml` to control pipeline behavior:

### Key Settings

- **Input Source**: Set `from_lta`, `from_fits`, or `from_multisrc_ms` to true
- **Calibration**: Configure `do_init_cal`, `do_flag`, `redo_cal`
- **Imaging**: Enable `make_dirty` and/or `do_selfcal`
- **Reference Antenna**: Set `ref_ant` (e.g., "C00")
- **Channel Averaging**: Adjust `chan_avg` (1 = no averaging)

## What Happens During Execution

The pipeline executes these steps automatically:

1. **Data Import** (if configured)
   - LTA → FITS conversion
   - FITS → MS import

2. **Flagging**
   - Initial flagging (first channel, quack)
   - Bad antenna detection

3. **Calibration**
   - Delay calibration
   - Bandpass calibration
   - Gain calibration
   - Flux scale computation

4. **Target Processing**
   - Split target data
   - Channel averaging

5. **Imaging** (if enabled)
   - Dirty image creation
   - Self-calibration loops
   - Final cleaned images

## Output Files

- **Log File**: `capture_HH_MM_SS_DD_MM_YYYY.log`
- **CASA Log**: `casa-capture_HH_MM_SS_DD_MM_YYYY.log`
- **Split MS**: Configured in `split_filename` or auto-generated
- **Images**: FITS files in working directory
- **Calibration Tables**: `*.K1`, `*.B1`, `*.AP.G`, `*.fluxscale`

## Example Workflow

```bash
# 1. Edit configuration
vim config_capture.toml

# 2. Run pipeline
python -m capture.main config_capture.toml --working-dir /data/observation1

# 3. Check logs for any issues
tail -f capture_*.log
```

## Common Issues

**Problem**: Module not found errors  
**Solution**: Make sure you're in the project root and CASA Python environment is active

**Problem**: No calibrators found  
**Solution**: Check your MS file has standard calibrator sources (3C48, 3C147, 3C286, etc.)

**Problem**: Missing output files  
**Solution**: Check the log file for errors; some steps may be skipped based on configuration

## Differences from Snakemake Version

- ✅ No need to install Snakemake
- ✅ Simpler execution model
- ✅ Better error messages
- ✅ Direct Python debugging support
- ⚠️ Steps run sequentially (no parallelization)
- ⚠️ Must complete all steps in one session

## Getting Help

Check the detailed documentation in `PIPELINE_CHANGES.md` for complete information about:
- All configuration options
- Step-by-step pipeline details
- Module structure
- Advanced usage
