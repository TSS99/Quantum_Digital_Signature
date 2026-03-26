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
