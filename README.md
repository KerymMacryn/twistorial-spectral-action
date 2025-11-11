# Twistorial Spectral Action — How to reproduce

This README gives the minimal, auditable steps to regenerate the manuscript’s key figures and tables (Fig. 8.1, Tables 8.1 / 11.1, the forecast notebook, and the twistor instanton example). It assumes you cloned the repository corresponding to the manuscript release (DOI: 10.5281/zenodo.17542581) and use the environment files provided in the repo.

## Quick summary
- Primary runner: `python scripts/DataFrames.py --also-scalars` (regenerates CSVs used for main tables)
- S4 heat-trace figure: `python notebooks/figures/plot_S4_heattrace.py --Nmax 100 --R 1`
- S4 coefficients (Table 8.1): `python notebooks/figures/compute_S4_coeffs.py --Nmax 100 --tmin 1e-4 --tmax 1e-2`
- Twistor instanton example (Appendix H): `python notebooks/scripts/run_twistor_instanton.py --N 200`
- Forecast pipeline (Sec. 7): `python notebooks/scripts/run_forecast.py --ER 1e-2 --transfer-set conservative`

## Reproducibility prerequisites
- Python 3.9 or 3.10 (3.10 recommended)
- Conda or virtualenv available
- Disk: ≥ 10 GB free for data and logs
- Memory: 16–64 GB recommended for full spectral runs; smaller tests run with 4–8 GB
- CPU: multi-core recommended; GPU is not required

Files to check before running:
- `environment.yml` (conda)
- `requirements.txt` (pip)
- `CHECKSUMS.txt` (file integrity)
- `scripts/` and `notebooks/` directories

## Environment setup

Option A — Conda (recommended)
```bash
conda env create -f environment.yml
conda activate twistorial-spec
```

Option B — venv + pip
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify environment (quick check)
```bash
python scripts/check_env.py
```
Expected output: list of key packages and versions matching the lock file.

## Data integrity check (smoke test)
Validate included data and packed artifacts against the provided checksums:
```bash
python scripts/check_checksums.py
```
Expected result: each file reported as `OK`. If a checksum fails, re-download the affected artifact from the release matching the DOI.

## One-command regeneration (recommended)
This single command regenerates the CSV tables used in the manuscript and stores runtime metadata for auditing:
```bash
python scripts/DataFrames.py --also-scalars
```
Outputs:
- `notebooks/data/*.csv` (tables for manuscript)
- `logs/run_manifest.json` (parameters, seeds, runtime, checksums)

Quick (fast) smoke run:
```bash
python scripts/DataFrames.py --quick
```
Produces a reduced set of CSVs and a short `logs/smoke_hashes.json`.

## Reproduce main figures and tables

Figure 8.1 — S4 heat-trace and running spectral dimension
```bash
python notebooks/figures/plot_S4_heattrace.py --Nmax 100 --R 1
```
Outputs:
- `figures/Fig_8_1.png`
- `logs/figure_8_1.json` (parameters: Nmax, t-window, tail method)

Table 8.1 — Recovered Seeley–DeWitt coefficients on S4
```bash
python notebooks/figures/compute_S4_coeffs.py --Nmax 100 --tmin 1e-4 --tmax 1e-2
```
Outputs:
- `notebooks/data/table_8_1.csv`
- console summary with best-fit values and fit residuals

Twistor instanton worked example (Appendix H)
Run notebook interactively:
```bash
jupyter nbconvert --to notebook --execute notebooks/worked_example_twistor_instanton.ipynb --ExecutePreprocessor.timeout=600 --output executed_twistor.ipynb
```
Or run the script headless:
```bash
python notebooks/scripts/run_twistor_instanton.py --N 200
```
Outputs:
- `notebooks/data/table_twistor_instanton.csv`
- `figures/Fig_twistor_conv.png`
Expected: relative error vs. topological integral ≤ 1% for standard discretisation.

Forecast pipeline (Sec. 7)
Interactive notebook:
```bash
jupyter nbconvert --to notebook --execute notebooks/worked_example_TSQVT_forecast_notebook.ipynb --ExecutePreprocessor.timeout=1200 --output executed_forecast.ipynb
```
Batch run:
```bash
python notebooks/scripts/run_forecast.py --ER 1e-2 --transfer-set conservative
```
Outputs:
- `notebooks/data/table_7_1.csv`
- `figures/forecast_summary.png`

## Audit checks and tests

Run unit tests / diagnostic scripts:
```bash
python scripts/tests/test_plateau_finder.py
python scripts/tests/test_tail_completion.py
```
Expected exit code 0 for passed tests.

Environment / package listing for audit:
```bash
python scripts/check_env.py > logs/env_versions.txt
```

Compare regenerated outputs with published outputs:
```bash
python scripts/compare_outputs.py --published-dir release_data/ --regenerated-dir notebooks/data/
```
This prints a short summary of numeric differences and indicates whether each difference is within the tolerance reported in the manuscript.

## Expected numeric tolerances (S4, Nmax=100, R=1)
- a0: ±0.001 (relative error ≲ 1%)
- a2: ±0.001 (relative error ≲ 1%)
- a4: ±0.0003 (relative error ≲ 0.2%)
If regenerations fall outside these tolerances, consult the diagnostics below.

## Common failure modes and remediation

- Import/package errors: recreate environment from `environment.yml` and re-run `python scripts/check_env.py`.
- Checksum mismatch: re-download the affected artifact from the release identified by DOI; verify `CHECKSUMS.txt`.
- Non-convergent fit or unstable plateau: adjust t-window (`--tmin`, `--tmax`), try `--tail-method local_weyl` or `--tail-method global_fit`, and re-run `compute_S4_coeffs.py`.
- High memory / long runtime: use `--quick` options for smoke tests or run on a larger CPU instance for full runs.
- Notebook timeout: increase `--ExecutePreprocessor.timeout` when running with nbconvert.

## Audit artifacts to include with a resubmission
When preparing a submission or response to reviewers include:
- `logs/run_manifest.json` (exact commands, seeds, environment hash, runtime)
- `notebooks/data/*.csv` for the main tables cited in the manuscript
- `figures/*.png` (publication resolution)
- `logs/env_versions.txt` and `CHECKSUMS.txt`
- `scripts/compare_outputs.py` output showing differences and tolerances

## Contact, DOI and repository
- Release DOI used for the manuscript: 10.5281/zenodo.17542581
- Repository mirror: https://github.com/KerymMacryn/twistorial-spectral-action
- If checks fail or files are missing: verify you are on the tag/release that corresponds to the DOI (see the repository releases page).

## Additional options (developer / advanced)
- Re-run the full spectral pipeline at higher resolution (increase `--Nmax`); be prepared for longer runtimes and higher memory usage.
- Switch tail-completion strategy via `--tail-method {local_weyl, global_fit}` to test sensitivity.
- Export figures in vector format by adding `--format pdf` to plotting scripts.

