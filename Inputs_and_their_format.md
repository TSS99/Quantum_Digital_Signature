# Inputs and Their Format

This document describes every input accepted by
`QuantumDigitalSignatureWithChannelNoise` (the constructor) and by the methods
that take arguments. All inputs are validated at construction time; an invalid
value raises `TypeError` or `ValueError` immediately.

---

## 1. Constructor inputs

`QuantumDigitalSignatureWithChannelNoise(...)`

| Parameter | Type | Default | Allowed values / format | Meaning |
|-----------|------|---------|-------------------------|---------|
| `message_bits` | `str` | *(required)* | Non-empty string of only `'0'` and `'1'`, e.g. `"101100"` | The classical message to be signed, one bit per position. |
| `n_qubits` | `int` | `4` | Integer `>= 1` and `<= L` | Number of qubits used to encode each public key. |
| `L` | `int` | `25` | Integer `>= 1` | Length (in bits) of each private key. |
| `M` | `int` | `5` | Integer `>= 1` | Number of independent public-key copies generated per message bit. |
| `c1` | `float` | `0.1` | `0 < c1 < c2 < 1` | Lower acceptance fraction. `ACCEPT` if failures `<= c1 * T`. |
| `c2` | `float` | `0.4` | `0 < c1 < c2 < 1` | Upper rejection fraction. `REJECT` if failures `>= c2 * T`. |
| `shots` | `int` | `4096` | Integer `>= 1` | Number of measurement repetitions per verification circuit. |
| `seed` | `int` | `42` | Any integer (not `bool`) | Seed for both the NumPy RNG and the Aer simulator (reproducibility). |
| `noise_channel` | `str` | `"none"` | One of: `none`, `depolarizing`, `amplitude_damping`, `phase_damping`, `bit_flip`, `phase_flip` (case-insensitive) | Type of quantum channel applied during public-key transmission. |
| `noise_probability` | `float` | `0.0` | `0.0 <= p <= 1.0` | Strength of the channel noise. |
| `verification_pass_threshold` | `float` | `0.80` | `0.0 <= t <= 1.0` | A single check passes if P(all-zero) after inverse verification is `>= t`. |
| `verbose` | `bool` | `True` | `True` / `False` | If `True`, prints JSON configuration/result events. |

### Format notes
- `message_bits` is a **string**, not a list. `"101100"` is valid; `[1,0,1]` is not.
- `T = len(message_bits) * M` is the total number of verification checks.
- `security_margin = L - n_qubits * M`. A non-positive value is allowed and is
  reported in the JSON `warnings` field.
- The simulator measures into a classical register, and Qiskit's all-zero count
  key is the string `"0" * n_qubits` (e.g. `"0000"` for 4 qubits).

### Example (valid)
```python
qds = QuantumDigitalSignatureWithChannelNoise(
    message_bits="101100",
    n_qubits=4,
    L=25,
    M=5,
    c1=0.1,
    c2=0.4,
    shots=4096,
    seed=42,
    noise_channel="depolarizing",
    noise_probability=0.05,
)
```

### Examples (rejected at construction)
```python
QuantumDigitalSignatureWithChannelNoise("12")          # ValueError: only '0'/'1'
QuantumDigitalSignatureWithChannelNoise("", )          # ValueError: empty
QuantumDigitalSignatureWithChannelNoise("10", c1=0.5, c2=0.4)  # ValueError: need c1 < c2
QuantumDigitalSignatureWithChannelNoise("10", noise_channel="gaussian")  # ValueError
QuantumDigitalSignatureWithChannelNoise("10", noise_probability=1.5)     # ValueError
QuantumDigitalSignatureWithChannelNoise("10", n_qubits=99, L=25)         # ValueError: n_qubits > L
```

---

## 2. Public method inputs

Only these instance methods are public. All other methods and stored state are
private implementation details.

### `run()`
No inputs. Runs the full honest workflow and returns a JSON string.

### `run_forgery_attempt()`
No inputs. Runs the workflow but verifies a forged (random-key) signature and
returns a JSON string.

### `run_swap_test_example(bit_index=0, copy_index=0, bit_value=None, make_plot=True)`
| Argument | Type | Format |
|----------|------|--------|
| `bit_index` | `int` | `0 <= bit_index < len(message_bits)` |
| `copy_index` | `int` | `0 <= copy_index < M` |
| `bit_value` | `int` or `None` | `0` or `1`; if `None`, uses the message bit at `bit_index` |
| `make_plot` | `bool` | Whether to include JSON bar-chart data in the returned payload |

### Private-key input (used internally by `_normalize_key`)
A private key may be given as:
- a **bit string** of length exactly `L`, e.g. `"0110...1"`, or
- an **iterable of bits** (ints or characters) of length exactly `L`.

Any other length, or characters outside `{'0','1'}`, raises `ValueError`.
