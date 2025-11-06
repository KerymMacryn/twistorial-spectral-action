# DataFrames.py — Ejecuta un notebook y exporta resultados a CSV (DFs + opcionalmente escalares/arrays)
# Uso:
#   python scripts/DataFrames.py
#   python scripts/DataFrames.py --nb ../notebooks/worked_example_TSQVT_forecast_notebook.ipynb --out ../notebooks/data --also-scalars
import argparse, json, os, re, numbers
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import nbformat
except Exception:
    nbformat = None

def read_notebook(path):
    """Lee el .ipynb como nbformat (si está) o JSON plano."""
    if nbformat is not None:
        try:
            return nbformat.read(path, as_version=4)
        except Exception:
            pass
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)

def sanitize_code(src: str) -> str:
    """Elimina magics (%) y llamadas shell (!) para ejecución pura de Python."""
    cleaned = []
    for line in src.splitlines():
        L = line.lstrip()
        if L.startswith("%") or L.startswith("!"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

class _DummyIP:
    def run_line_magic(self, *args, **kwargs): pass
    def run_cell_magic(self, *args, **kwargs): pass
    def magic(self, *args, **kwargs): pass

def get_ipython():
    # Para notebooks que invocan get_ipython()
    return _DummyIP()

def sanitize_name(name: str) -> str:
    """Nombre de archivo seguro."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name)).strip("_.") or "var"

def exec_notebook(nb_path: Path):
    """Ejecuta el notebook y devuelve (namespace, errores, num_celdas)."""
    nb = read_notebook(str(nb_path))
    cells = []
    nb_cells = nb["cells"] if isinstance(nb, dict) else nb.cells
    for c in nb_cells:
        if c.get("cell_type") == "code":
            src = c.get("source", "")
            if src:
                cells.append(sanitize_code(src))
    g = {"__name__": "__main__", "get_ipython": get_ipython}
    code = "\n\n# --- cell ---\n\n".join(cells)
    errors = []
    try:
        exec(compile(code, str(nb_path), "exec"), g, g)
    except Exception as e:
        errors.append(f"Execution error: {e}")
    return g, errors, len(cells)

def export_dataframes(ns: dict, out_dir: Path):
    """Exporta todos los DataFrames en el namespace."""
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for k, v in list(ns.items()):
        if isinstance(v, pd.DataFrame):
            name = sanitize_name(k)
            dest = out_dir / f"{name}.csv"
            try:
                v.to_csv(dest, index=False)
                exported.append(str(dest))
            except Exception as e:
                print(f"[WARN] No se pudo exportar DataFrame {k}: {e}")
    return exported

def export_scalars_and_arrays(ns: dict, out_dir: Path, max_array_len: int = 100000):
    """Exporta escalares y arrays 1D (numpy/Series) a CSVs. Devuelve (scalars_csv, arrays_exported)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    scalars = []
    arrays = []

    for k, v in list(ns.items()):
        if k.startswith("_"):
            continue
        # Escalares simples
        if isinstance(v, numbers.Number) or isinstance(v, (str, bool)):
            if isinstance(v, str) and len(v) > 200:
                continue
            scalars.append({"name": k, "value": v, "type": type(v).__name__})
        # Arrays 1D
        try:
            if hasattr(v, "shape"):
                shp = getattr(v, "shape", ())
                if len(shp) == 1 and 0 < shp[0] <= max_array_len:
                    arr = np.asarray(v)
                    name = sanitize_name(k)
                    df = pd.DataFrame({name: arr})
                    df.to_csv(out_dir / f"{name}.csv", index=False)
                    arrays.append(str(out_dir / f"{name}.csv"))
            elif isinstance(v, pd.Series):
                name = sanitize_name(k)
                v.to_csv(out_dir / f"{name}.csv", index=False)
                arrays.append(str(out_dir / f"{name}.csv"))
        except Exception as e:
            print(f"[WARN] No se pudo exportar array 1D {k}: {e}")

    scalars_csv = None
    if scalars:
        scalars_df = pd.DataFrame(scalars).sort_values("name")
        scalars_csv = out_dir / "forecast_scalars.csv"
        scalars_df.to_csv(scalars_csv, index=False)
        scalars_csv = str(scalars_csv)

    return scalars_csv, arrays

def main():
    parser = argparse.ArgumentParser(description="Ejecuta un notebook y exporta resultados a CSV.")
    parser.add_argument("--nb", type=str, default="../notebooks/worked_example_TSQVT_forecast_notebook.ipynb",
                        help="Ruta al notebook .ipynb")
    parser.add_argument("--out", type=str, default="../notebooks/data",
                        help="Directorio de salida para CSVs")
    parser.add_argument("--also-scalars", action="store_true",
                        help="Exportar también escalares/arrays aunque existan DataFrames")
    parser.add_argument("--max-array-len", type=int, default=100000,
                        help="Tamaño máximo permitido para arrays 1D a exportar")
    args = parser.parse_args()

    nb_path = Path(args.nb).resolve()
    out_dir = Path(args.out).resolve()
    if not nb_path.exists():
        raise FileNotFoundError(f"No existe el notebook: {nb_path}")

    print(f"[INFO] Notebook: {nb_path}")
    print(f"[INFO] Output dir: {out_dir}")
    print(f"[INFO] also-scalars: {args.also_scalars}")

    ns, exec_errors, ncode = exec_notebook(nb_path)
    if exec_errors:
        print("[WARN] Errores durante la ejecución:")
        for e in exec_errors:
            print("  -", e)

    df_exports = export_dataframes(ns, out_dir)

    scalars_csv = None
    arrays_exports = []
    if args.also_scalars or not df_exports:
        scalars_csv, arrays_exports = export_scalars_and_arrays(ns, out_dir, max_array_len=args.max_array_len)

    summary = {
        "notebook": str(nb_path),
        "code_cells": ncode,
        "dataframes_exported": df_exports,
        "scalars_csv": scalars_csv,
        "arrays_exported": arrays_exports,
        "output_dir": str(out_dir),
        "warnings": exec_errors,
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
