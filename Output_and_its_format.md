# Output and Its Format

This document describes what the public methods `run()`,
`run_forgery_attempt()`, and `run_swap_test_example()` return, plus the printed
summary.

---

## 1. The verification result dictionary

`run()` and `run_forgery_attempt()` both return a single dictionary with this
shape:

```python
{
    "message_bits": "101100",        # str  - the signed message
    "n_qubits": 4,                    # int
    "L": 25,                          # int  - private-key length
    "M": 5,                           # int  - copies per bit
    "c1": 0.1,                        # float
    "c2": 0.4,                        # float
    "shots": 4096,                    # int
    "seed": 42,                       # int
    "noise_channel": "depolarizing",  # str
    "noise_probability": 0.05,        # float
    "security_margin": 5,             # int  - L - n_qubits*M

    "total_verifications": 30,        # int  - T = len(message)*M
    "failed_verifications": 0,        # int  - s = number of failed checks
    "failure_rate": 0.0,              # float - s / T
    "authentic_threshold": 3.0,       # float - c1*T
    "reject_threshold": 12.0,         # float - c2*T
    "verdict": "ACCEPT_AUTHENTIC",    # str  - see below

    "per_bit_results": { ... },       # dict - detail per message-bit position
    "raw_counts_summary": [ ... ],    # list - raw measurement counts per check
}
```

### `verdict` field
Exactly one of three string constants:

| Verdict | Condition | Meaning |
|---------|-----------|---------|
| `"ACCEPT_AUTHENTIC"` | `s <= c1 * T` | Few enough failures; signature accepted. |
| `"REJECT_FORGED"` | `s >= c2 * T` | Too many failures; signature rejected. |
| `"INCONCLUSIVE"` | `c1*T < s < c2*T` | In between; verdict withheld. |

where `s = failed_verifications` and `T = total_verifications`.

### `per_bit_results` field
A dict keyed by integer bit index (`0 .. len(message)-1`):

```python
0: {
    "bit_value": 1,                # int  - the signed bit at this position
    "failed_verifications": 0,     # int  - failures among the M copies
    "failure_rate": 0.0,           # float - failed / M
    "copy_results": [
        {
            "copy_index": 0,                   # int
            "zero_state_probability": 1.0,     # float - P(all-zero)
            "passed": True,                    # bool  - prob >= threshold
            "counts": {"0000": 4096},          # dict  - raw measurement counts
        },
        ...  # M entries
    ],
}
```

### `raw_counts_summary` field
A flat list (length `T`) of per-check records, useful for plotting or auditing:

```python
{
    "bit_index": 0,
    "bit_value": 1,
    "copy_index": 0,
    "counts": {"0000": 4096},   # measurement histogram, key = bitstring
}
```

**Counts format:** `counts` is a Qiskit histogram — keys are measured
bitstrings, values are how many of the `shots` landed there. The all-pass key is
`"0" * n_qubits`. In a noiseless honest run every check yields `{"0000": 4096}`.

---

## 2. Printed summary (when `verbose=True`)

`run()` prints this summary when `verbose=True`, e.g.:

```
Protocol summary
------------------------------------------------
message_bits            : 101100
noise                   : depolarizing (p=0.05)
security_margin         : 5
total_verifications     : 30
failed_verifications    : 0
failure_rate            : 0.0000
authentic_threshold     : 3.00
reject_threshold        : 12.00
verdict                 : ACCEPT_AUTHENTIC
```

A forgery attempt prints the same block with `verdict : REJECT_FORGED` and
`failed_verifications : 30`.

---

## 3. `run_swap_test_example(...)` output

Returns:
```python
{
    "bit_index": 0,
    "copy_index": 0,
    "bit_value": 1,
    "comparisons": {
        "ideal_vs_ideal":         {"p_ancilla_zero": ~1.0,  "counts": {...}, "circuit": <QuantumCircuit>},
        "ideal_vs_received":      {"p_ancilla_zero": ~0.9x, "counts": {...}, "circuit": <QuantumCircuit>},
        "ideal_vs_complementary": {"p_ancilla_zero": ~0.5x, "counts": {...}, "circuit": <QuantumCircuit>},
    },
}
```
- `p_ancilla_zero` is the SWAP-test estimate of state overlap:
  `P(ancilla=0) = (1 + |<a|b>|^2) / 2`.
- `ideal_vs_ideal` is ~1.0 (identical states), `ideal_vs_complementary`
  approaches ~0.5 (nearly orthogonal), and `ideal_vs_received` sits in between
  depending on noise.
- If `make_plot=True`, a Matplotlib bar chart is also displayed.

---

## 4. Errors as output

Invalid input does not return a value — it raises:
- `TypeError` for wrong types (e.g. non-integer `n_qubits`, non-string `message_bits`).
- `ValueError` for out-of-range values (e.g. `c1 >= c2`, unknown `noise_channel`,
  wrong private-key length).
- `RuntimeError` if verification is attempted before keys/public keys exist.
