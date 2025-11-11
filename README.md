
# Twistorial Spectral Action — How to reproduce

This README provides **minimal, auditable steps** to regenerate the manuscript’s key figures and tables, and to run the new **spectral-signature Σ benchmark**.  
Use the **GitHub release/tag that matches the DOI** you intend to reproduce:

- **Manuscript release DOI:** `10.5281/zenodo.17542581`  
- **Sigma benchmark (finite-N) DOI:** `10.5281/zenodo.17580885`

> Tip: Check the **Releases** page on GitHub and switch to the tag corresponding to the DOI above.

---

## Quick summary

- **Main CSV regeneration:**
  ```bash
  python scripts/DataFrames.py --also-scalars
````

* **S⁴ heat-trace figure:**

  ```bash
  python notebooks/figures/plot_S4_heattrace.py --Nmax 100 --R 1
  ```

* **S⁴ coefficients (Table 8.1):**

  ```bash
  python notebooks/figures/compute_S4_coeffs.py --Nmax 100 --tmin 1e-4 --tmax 1e-2
  ```

* **Twistor instanton example (Appendix H):**

  ```bash
  python notebooks/scripts/run_twistor_instanton.py --N 200
  ```

* **Forecast pipeline (Sec. 7):**

  ```bash
  python notebooks/scripts/run_forecast.py --ER 1e-2 --transfer-set conservative
  ```

* **NEW — Spectral-signature Σ (finite-N):**

  ```bash
  python scripts/spectral_signature_sigma.py
  ```

---

## Reproducibility prerequisites

* Python 3.9–3.11 (**3.10** recommended)
* Conda or virtualenv
* Disk: ≥ 10 GB free (data + logs)
* RAM: 16–64 GB recommended for full spectral runs (smoke tests: 4–8 GB)
* CPU: multi-core recommended; **no GPU required**

**Files to check before running:**

* `environment.yml` (conda) / `requirements.txt` (pip)
* `scripts/CHECKSUMS.txt` (file integrity)
* `scripts/` and `notebooks/` present

---

## Environment setup

**Option A — Conda (recommended)**

```bash
conda env create -f environment.yml
conda activate twistorial-spec
```

**Option B — venv + pip**

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

**Verify environment**

```bash
python scripts/check_env.py
```

Expected: list of key packages/versions matching the lock file.

---

## Data integrity check (smoke test)

Validate included data and packed artifacts:

```bash
python scripts/check_checksums.py
```

Expected: each file reported as `OK`. If a checksum fails, re-download the affected asset from the **release matching the DOI**.

---

## One-command regeneration (recommended)

Regenerate manuscript CSV tables and store runtime metadata:

```bash
python scripts/DataFrames.py --also-scalars
```

Outputs:

* `notebooks/data/*.csv` (tables used in the manuscript)
* `logs/run_manifest.json` (parameters, seeds, runtime, checksums)

**Quick smoke run**

```bash
python scripts/DataFrames.py --quick
```

Outputs a reduced CSV set and `logs/smoke_hashes.json`.

---

## Reproduce main figures and tables

**Figure 8.1 — S⁴ heat-trace & running spectral dimension**

```bash
python notebooks/figures/plot_S4_heattrace.py --Nmax 100 --R 1
```

Outputs:

* `figures/Fig_8_1.png`
* `logs/figure_8_1.json` (Nmax, t-window, tail method)

**Table 8.1 — Seeley–DeWitt coefficients on S⁴**

```bash
python notebooks/figures/compute_S4_coeffs.py --Nmax 100 --tmin 1e-4 --tmax 1e-2
```

Outputs:

* `notebooks/data/table_8_1.csv`
* Console summary with best-fit values and residuals

**Twistor instanton worked example (Appendix H)**

Interactive:

```bash
jupyter nbconvert --to notebook --execute notebooks/worked_example_twistor_instanton.ipynb \
  --ExecutePreprocessor.timeout=600 --output executed_twistor.ipynb
```

Headless:

```bash
python notebooks/scripts/run_twistor_instanton.py --N 200
```

Outputs:

* `notebooks/data/table_twistor_instanton.csv`
* `figures/Fig_twistor_conv.png`
  Expected: relative error vs. topological integral ≤ 1% (standard discretization).

**Forecast pipeline (Sec. 7)**

Interactive:

```bash
jupyter nbconvert --to notebook --execute notebooks/worked_example_TSQVT_forecast_notebook.ipynb \
  --ExecutePreprocessor.timeout=1200 --output executed_forecast.ipynb
```

Batch:

```bash
python notebooks/scripts/run_forecast.py --ER 1e-2 --transfer-set conservative
```

Outputs:

* `notebooks/data/table_7_1.csv`
* `figures/forecast_summary.png`

---

## NEW: Spectral-signature Σ benchmark (finite-N)

Verifies chiral symmetry pairing under `SDS = -D`, stability under `SVS = -V`, and unitary covariance (`[U,S] = 0`).

Run:

```bash
python scripts/spectral_signature_sigma.py
```

Expected (double precision, typical `N`): traces ≈ 0 within ≲ 1e−11; paired sums ≲ 1e−12.
Outputs (also persisted with metadata):

* `results/spectral_signature_sigma_*.json` / `*.csv`

**Citable archive (Zenodo):** DOI `10.5281/zenodo.17580885`
Release artifacts include JSON/CSV outputs and the script.

---

## Audit checks and tests

**Unit tests / diagnostics**

```bash
python scripts/tests/test_plateau_finder.py
python scripts/tests/test_tail_completion.py
```

Expected exit code `0`.

**Environment/package listing**

```bash
python scripts/check_env.py > logs/env_versions.txt
```

**Compare regenerated vs. published outputs**

```bash
python scripts/compare_outputs.py --published-dir release_data/ --regenerated-dir notebooks/data/
```

Prints numeric differences and whether they are within manuscript tolerances.

---

## Expected numeric tolerances (S⁴, Nmax = 100, R = 1)

* `a_0`: ±0.001  (relative error ≲ 1%)
* `a_2`: ±0.001  (relative error ≲ 1%)
* `a_4`: ±0.0003 (relative error ≲ 0.2%)

If outside tolerances, see **Common failure modes**.

---

## Common failure modes and remediation

* **Import/package errors:** recreate env from `environment.yml`, then re-run `scripts/check_env.py`.
* **Checksum mismatch:** re-download the asset from the **matching DOI**; re-run `check_checksums.py`.
* **Non-convergent fit / unstable plateau:** adjust `--tmin/--tmax`; try `--tail-method local_weyl` or `--tail-method global_fit`.
* **High memory / long runtime:** use `--quick` for smoke tests, or use a larger CPU instance for full runs.
* **Notebook timeout:** increase `--ExecutePreprocessor.timeout` when using `nbconvert`.
* **Windows line endings:** repository is normalized to **LF**; Git may warn about CRLF→LF—this is harmless.

---

## Audit artifacts to include with a resubmission

* `logs/run_manifest.json` (exact commands, seeds, env hash, runtime)
* `notebooks/data/*.csv` (tables cited)
* `figures/*.png` (publication resolution)
* `logs/env_versions.txt` and `scripts/CHECKSUMS.txt`
* Output of `scripts/compare_outputs.py` showing diffs/tolerances

---

## Contact, DOIs, and repository

* **Manuscript release DOI:** `10.5281/zenodo.17542581`
* **Sigma benchmark DOI:** `10.5281/zenodo.17580885`
* **Repository:** [https://github.com/KerymMacryn/twistorial-spectral-action](https://github.com/KerymMacryn/twistorial-spectral-action)

> If checks fail or files are missing: verify you’re on the tag/release corresponding to the DOI (see GitHub Releases).

---

## Advanced options

* Increase resolution (e.g., `--Nmax`) for full spectral runs (higher runtime/memory).
* Switch tail completion via `--tail-method {local_weyl,global_fit}` to test sensitivity.
* Export vector figures with `--format pdf`.

[![DOI (Sigma benchmark)](https://zenodo.org/badge/DOI/10.5281/zenodo.17580885.svg)](https://doi.org/10.5281/zenodo.17580885)
[![DOI (Manuscript release)](https://zenodo.org/badge/DOI/10.5281/zenodo.17542581.svg)](https://doi.org/10.5281/zenodo.17542581)

```
```
