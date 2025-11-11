# Minimal benchmark for spectral signature Sigma (finite-N) spectral_signature_sigma.py
# Requires: numpy, scipy
# pip install numpy scipy

import numpy as np
from scipy.linalg import eigh, expm
import math

# ----------------------
# Parameters (tunable)
# ----------------------
N_block = 300          # block size; total dimension will be 2*N_block
N = 2 * N_block
seed = 2025
Lambda = 5.0           # regulator scale in f(x) = x * exp(-x^2 / Lambda^2)
perturb_eps = 1e-2     # amplitude of symmetric perturbation V
unitary_eps = 1e-1     # amplitude for generating unitary that commutes with S

np.random.seed(seed)

# ----------------------
# Build involutive unitary S (block-diagonal with +I, -I)
# S^2 = I, S = S^\dagger
S = np.block([
    [np.eye(N_block), np.zeros((N_block, N_block))],
    [np.zeros((N_block, N_block)), -np.eye(N_block)]
])

# ----------------------
# Construct D with S D S = -D
# A simple choice: off-diagonal block matrix
# D = [[0, A],
#      [A^T, 0]]
A = np.random.normal(scale=1.0, size=(N_block, N_block))
# Make A symmetric to ensure D Hermitian: use (A + A^T)/2
A = 0.5 * (A + A.T)
D = np.block([
    [np.zeros((N_block, N_block)), A],
    [A.T, np.zeros((N_block, N_block))]
])

# Quick check of the symmetry S D S = -D (numerical)
assert np.allclose(S @ D @ S, -D, atol=1e-10)

# ----------------------
# Define regulator function f(x) = x * exp(-x^2 / Lambda^2)
# Compute f(D) via spectral decomposition
evals, evecs = eigh(D)  # eigendecomposition: D = evecs @ diag(evals) @ evecs.T
f_vals = evals * np.exp(-(evals**2) / (Lambda**2))
# Reconstruct f(D) (trace-class finite matrix)
fD = (evecs * f_vals) @ evecs.T.conj()

trace_fD = np.trace(fD).real
print(f"Trace Tr[f(D)] (unperturbed) = {trace_fD:.3e}")

# Also inspect the eigenvalue pairing (max asymmetry)
# Pairing: for each positive eigenvalue find corresponding negative
# A simple check: sum of eigenvalues of f(D) should be ~0
sum_f_eigs = np.sum(f_vals)
print(f"Sum of f(eigenvalues) (should match trace) = {sum_f_eigs:.3e}")
print(f"Max |f(lambda_i) + f(lambda_j)| for paired indices? (approx):")
# Since spectrum is symmetric, f_vals should be anti-symmetric; check max of f(λ)+f(-λ)
# Sort evals and pair symmetric ones by sign
pos_idx = np.where(evals > 0)[0]
neg_idx = np.where(evals < 0)[0]
# Match counts may differ by zero modes: check max absolute sum of matched magnitudes
if len(pos_idx) == len(neg_idx):
    paired_sum_max = np.max(np.abs(f_vals[pos_idx] + f_vals[neg_idx[::-1]]))
    print(f"  paired max |f(λ)+f(-λ)| = {paired_sum_max:.3e}")
else:
    print("  unequal counts of pos/neg eigenvalues (zero modes present)")

# ----------------------
# Apply symmetric perturbation V with S V S = -V
# Build V in same off-diagonal form scaled by perturb_eps
B = np.random.normal(scale=1.0, size=(N_block, N_block))
B = 0.5 * (B + B.T)
V = perturb_eps * np.block([
    [np.zeros((N_block, N_block)), B],
    [B.T, np.zeros((N_block, N_block))]
])
assert np.allclose(S @ V @ S, -V, atol=1e-12)

D_pert = D + V
evals_p, evecs_p = eigh(D_pert)
f_vals_p = evals_p * np.exp(-(evals_p**2) / (Lambda**2))
fD_p = (evecs_p * f_vals_p) @ evecs_p.T.conj()
trace_fD_p = np.trace(fD_p).real
print(f"Trace Tr[f(D + V)] (perturbed symmetric V) = {trace_fD_p:.3e}")
print(f"Difference trace (perturbed - unperturbed) = {(trace_fD_p - trace_fD):.3e}")

# ----------------------
# Apply unitary U that commutes with S and conjugate D -> U D U^\dagger
# Construct U as exp(i * epsilon * H) where H is block-diagonal to commute with S
H_top = np.random.normal(size=(N_block, N_block))
H_top = 0.5 * (H_top + H_top.T)  # symmetric real => Hermitian block
H_bottom = np.random.normal(size=(N_block, N_block))
H_bottom = 0.5 * (H_bottom + H_bottom.T)
H = np.block([
    [H_top, np.zeros((N_block, N_block))],
    [np.zeros((N_block, N_block)), H_bottom]
])
# This H commutes with S (because it is block-diagonal), so U will too
U = expm(1j * unitary_eps * H)
# Check commutation [U, S] ≈ 0
comm_norm = np.linalg.norm(U @ S - S @ U)
print(f"||[U,S]|| = {comm_norm:.3e} (should be ~0)")

D_U = U @ D @ U.conj().T
evals_u, evecs_u = eigh(D_U)
f_vals_u = evals_u * np.exp(-(evals_u**2) / (Lambda**2))
fD_u = (evecs_u * f_vals_u) @ evecs_u.T.conj()
trace_fD_u = np.trace(fD_u).real
print(f"Trace Tr[f(U D U^†)] = {trace_fD_u:.3e}")
print(f"Difference trace (unitary conj - unperturbed) = {(trace_fD_u - trace_fD):.3e}")

# ----------------------
# Summary checks and optional diagnostics
print("\nSummary:")
print(f"  Tr[f(D)]                = {trace_fD:.3e}")
print(f"  Tr[f(D + V)]            = {trace_fD_p:.3e}")
print(f"  Tr[f(U D U^†)]         = {trace_fD_u:.3e}")
print("Expected: values ~ 0 and differences ≈ 0 (up to numerical roundoff).")

# Optional: plot eigenvalue distributions or histograms if matplotlib available
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(6,3))
    plt.hist(evals, bins=100, alpha=0.6, label='D eigenvalues')
    plt.hist(evals_p, bins=100, alpha=0.4, label='D+V eigenvalues')
    plt.legend()
    plt.title('Eigenvalue distributions (D vs D+V)')
    plt.tight_layout()
    plt.show()
except Exception:
    pass
    
# --- Persist results with metadata ---
import json, csv, platform, subprocess, datetime, os, sys
os.makedirs("results", exist_ok=True)

def safe_git(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "NA"

run = {
    "timestamp": datetime.datetime.now().isoformat(),
    "commit": safe_git(["git","rev-parse","HEAD"]),
    "branch": safe_git(["git","rev-parse","--abbrev-ref","HEAD"]),
    "python": sys.version.replace("\n"," "),
    "numpy": np.__version__,
    "scipy":  __import__("scipy").__version__,
    "platform": platform.platform(),
    "N_block": int(N_block), "N": int(N),
    "seed": int(seed), "Lambda": float(Lambda),
    "perturb_eps": float(perturb_eps), "unitary_eps": float(unitary_eps),
    "trace_fD": float(trace_fD),
    "trace_fD_pert": float(trace_fD_p),
    "trace_fD_U": float(trace_fD_u),
    "sum_f_eigs": float(sum_f_eigs),
    "paired_max": float(paired_sum_max if len(pos_idx)==len(neg_idx) else float("nan")),
    "comm_norm": float(comm_norm)
}

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = f"results/spectral_signature_sigma_{stamp}.json"
csv_path  = f"results/spectral_signature_sigma_{stamp}.csv"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(run, f, indent=2)

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(run.keys()); w.writerow(run.values())

print(f"\nSaved: {json_path}\nSaved: {csv_path}")
