# Quantum Digital Signature (QDS)

A Python implementation of the **Gottesman-Chuang Quantum Digital Signature** scheme — a way to sign messages using the laws of quantum physics instead of traditional math-based cryptography.

> Based on: D. Gottesman & I. L. Chuang, *"Quantum Digital Signatures"*, arXiv:quant-ph/0105032 (2001)

---

## What Is This?

A **digital signature** is a way for someone (Alice) to prove she sent a message — and that the message wasn't tampered with. Normally this relies on hard math problems (like factoring large numbers).

This project implements a **quantum** version: security comes from the laws of quantum physics itself — specifically, the fact that you can't perfectly copy an unknown quantum state (the **no-cloning theorem**) and that quantum measurements disturb the system you're measuring (**Holevo's theorem**).

Even a quantum computer can't break this scheme.

---

## How the Protocol Works (Simple Version)

```
Alice                              Bob / Charlie
  |                                      |
  |-- Key Generation ------------------>|
  |   For each message bit:             |
  |   - Creates private keys k0, k1     |
  |   - Creates quantum states |f_k0>,  |
  |     |f_k1> from each key            |
  |   - Sends quantum states to Bob --->|
  |                                     |
  |                                     |-- Swap Test (verification)
  |                                     |   Checks quantum states are
  |                                     |   consistent copies
  |                                     |
  |-- Signing ------------------------->|
  |   Reveals private key for each bit  |
  |   (keeps the other key secret)      |
  |                                     |
  |                                  Bob verifies:
  |                                  - Reconstructs quantum state
  |                                    from revealed key
  |                                  - Counts failures (s_j)
  |                                  - Accepts or rejects
```

**Three possible verdicts:**

| Result | Meaning |
|--------|---------|
| **1-ACC** | Valid signature — Bob can pass it to Charlie |
| **0-ACC** | Valid signature — but Bob must keep it himself |
| **REJ**   | Signature is fake — reject it |

---

## The Math (Bird's-Eye View)

Each private key `k` (a string of bits) is mapped to a quantum state using a rotation gate:

```
|f_k⟩ = cos(j·θ)|0⟩ + sin(j·θ)|1⟩
```

where `j = int(k, 2)` and `θ = π / 2^L`.

This is done with a single `RY` gate in Qiskit:

```
RY(2·j·θ)|0⟩  →  cos(j·θ)|0⟩ + sin(j·θ)|1⟩
```

Checking if two quantum states match uses the **SWAP test** circuit:

```
P(ancilla = |0⟩) = (1 + |⟨a|b⟩|²) / 2
```

- Same states → P = 1.0
- Totally different states → P = 0.5

---

## Project Structure

```
Quantum_Digital_Signature/
│
├── quantum_digital_signature.ipynb   ← Main notebook (start here!)
│
├── example_circuit.png               ← Diagram of one key-generation circuit
├── swap_test_comparison.png          ← Bar chart: SWAP test results
├── verification_decision.png         ← Decision zones for signature verdict
└── forgery_analysis.png              ← Security graph: P(forgery) vs M
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher ([download here](https://www.python.org/downloads/))
- Git (optional, for cloning)

You do **not** need a quantum computer — everything runs on a simulator.

---

### Step 1 — Clone or Download

```bash
git clone <your-repo-url>
cd Quantum_Digital_Signature
```

Or just download and unzip the folder.

---

### Step 2 — Create a Virtual Environment

A virtual environment keeps the project's packages separate from your system Python.

```bash
# Create the environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal — that means it's active.

---

### Step 3 — Install Required Packages

```bash
pip install qiskit qiskit-aer numpy scipy matplotlib ipykernel jupyter pylatexenc
```

This installs:

| Package | What it does |
|---------|-------------|
| `qiskit` | IBM's quantum computing framework |
| `qiskit-aer` | Fast quantum circuit simulator (no real quantum hardware needed) |
| `numpy` | Math and array operations |
| `scipy` | Scientific computing |
| `matplotlib` | Plotting graphs |
| `ipykernel` | Lets Jupyter use our virtual environment |
| `jupyter` | Run the notebook |
| `pylatexenc` | Lets Qiskit draw circuit diagrams |

---

### Step 4 — Register the Jupyter Kernel

This tells Jupyter to use the packages we just installed:

```bash
python -m ipykernel install --user --name QDS-env --display-name "QDS-env"
```

---

### Step 5 — Open the Notebook

```bash
jupyter notebook quantum_digital_signature.ipynb
```

Your browser will open. Make sure the kernel (top-right corner) is set to **QDS-env**.

Then run all cells: **Kernel → Restart & Run All**

---

## What You'll See in the Notebook

The notebook walks through the full protocol step by step:

1. **Library imports** — loads Qiskit, NumPy, Matplotlib
2. **The `QuantumDigitalSignature` class** — all the logic lives here
3. **Message input** — `"101100101"` as a test message
4. **Key generation** — private keys + quantum public-key circuits
5. **Circuit diagram** — visual of one `RY` gate circuit
6. **SWAP test** — bar chart comparing identical vs different states
7. **Signature generation** — Alice reveals private keys
8. **Verification** — check revealed keys, count failures, print verdict
9. **Security sweep** — graph showing forgery probability drops exponentially with M

---

## Security Parameters Explained

| Parameter | Symbol | What it means |
|-----------|--------|---------------|
| Key length | `L` | Bits in each private key. Larger = more secure |
| Copies per bit | `M` | How many key pairs per message bit. Larger = harder to forge |
| Qubits per state | `n` | Size of each quantum public key |
| Overlap bound | `δ` | How different two quantum states must be. Smaller = more secure |

**Security rule of thumb:** `L - n×M >> 1`

In the notebook demo: `L=6, n=1, M=5` → `L - n×M = 1` (just enough for demonstration).
In a real deployment, use `L=32` or larger.

---

## Running the Notebook from the Command Line

If you prefer not to open a browser:

```bash
venv/Scripts/python.exe -m jupyter nbconvert \
    --to notebook \
    --execute \
    --ExecutePreprocessor.timeout=300 \
    --ExecutePreprocessor.kernel_name=qds-env \
    --output output.ipynb \
    quantum_digital_signature.ipynb
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'qiskit'` | Run `pip install qiskit` with venv active |
| Kernel not showing as "QDS-env" | Re-run the `ipykernel install` command in Step 4 |
| `MissingOptionalLibraryError: pylatexenc` | Run `pip install pylatexenc` |
| Plots not showing | Make sure the first cell ran successfully (`%matplotlib inline`) |
| Notebook runs slowly | Reduce `M` from `5` to `2` or `3` in Cell 6 |

---

## References

1. Gottesman, D. & Chuang, I. L. (2001). *Quantum Digital Signatures*. [arXiv:quant-ph/0105032](https://arxiv.org/abs/quant-ph/0105032)
2. Nielsen, M. A. & Chuang, I. L. (2010). *Quantum Computation and Quantum Information*. Cambridge University Press.
3. Qiskit Documentation: [https://docs.quantum.ibm.com](https://docs.quantum.ibm.com)

---

## Repository Update History

- Update 1: Documented repository structure and verified setup.
- Update 2: Verified QDS execution with noise parameters.
- Update 3: Verified QDS execution with noise parameters.
- Update 4: Verified QDS execution with noise parameters.
