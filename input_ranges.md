# QDS Input Range Guide

This document describes the accepted inputs, validation constraints, recommended values, and the exact minimum and maximum limits for every parameter in the Gottesman-Chuang style Quantum Digital Signature (QDS) protocol implementation.

---

## 1. Constructor Parameters

These parameters are configured when initializing the `QuantumDigitalSignatureWithChannelNoise` class:

| Parameter | Type | Default | Absolute Min Value / Constraint | Absolute Max Value / Constraint | Recommended Range (Aer Optimized) | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`message_bits`** | `str` | *(Required)* | Length $\ge 1$<br>(Characters must be only `'0'` or `'1'`) | None (restricted by hardware/memory) | Length $1$ to $100$ | The binary message to be signed. |
| **`n_qubits`** | `int` | `4` | $1$ | $L$ (cannot exceed private key length) | $2$ to $8$ | Number of qubits used to encode each public-key state. |
| **`L`** | `int` | `25` | $\text{n\_qubits}$ | None (restricted by hardware/precision) | $100$ to $250$ | Bit-length of each private key string. |
| **`M`** | `int` | `5` | $1$ | None (restricted by hardware/memory) | $3$ to $10$ | Number of independent public-key copies per message bit. |
| **`c1`** | `float` | `0.1` | $> 0.0$ (exclusive) | $< c2$ (exclusive) | $0.05$ to $0.15$ | Lower authentic acceptance threshold fraction. |
| **`c2`** | `float` | `0.4` | $> c1$ (exclusive) | $< 1.0$ (exclusive) | $0.30$ to $0.50$ | Upper forgery rejection threshold fraction. |
| **`shots`** | `int` | `4096` | $1$ | None (restricted by hardware/time) | $1024$ to $8192$ | Repetitions per verification circuit measurement. |
| **`seed`** | `int` | `42` | Minimum system integer | Maximum system integer | $0$ to $10^6$ | Random seed for simulation/key reproducibility. |
| **`noise_channel`** | `str` | `"none"` | Must be one of:<br>`"none"`, `"depolarizing"`, `"amplitude_damping"`, `"phase_damping"`, `"bit_flip"`, `"phase_flip"` (case-insensitive) | N/A | N/A | Type of quantum noise applied to public-key qubits. |
| **`noise_probability`** | `float` | `0.0` | $0.0$ | $1.0$ | $0.0$ to $0.20$ | Probability strength parameter for the noise channel. |
| **`verification_pass_threshold`** | `float` | `0.80` | $0.0$ | $1.0$ | $0.70$ to $0.90$ | Min all-zero probability for a check copy to pass. |
| **`verbose`** | `bool` | `True` | `False` | `True` | N/A | Enables console logging/printing of JSON events. |

---

## 2. Public Method Parameters

### `run_swap_test_example(...)`

This method compares public-key states using a SWAP-test circuit:

| Parameter | Type | Default | Absolute Min Value / Constraint | Absolute Max Value / Constraint | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`bit_index`** | `int` | `0` | `0` | $\text{len}(message\_bits) - 1$ | Message bit position to compare. |
| **`copy_index`** | `int` | `0` | `0` | $M - 1$ | Stored public-key copy number to compare. |
| **`bit_value`** | `int` or `None` | `None` | `0` | `1` | Specific key value to compare; if `None`, defaults to the actual message bit at `bit_index`. |
| **`make_plot`** | `bool` | `True` | `False` | `True` | Whether to include plot data in the returned JSON. |

---

## 3. Aer Simulator Optimization Details

* **Qubit Count (`n_qubits`):** Keep $\text{n\_qubits} \le 8$. Since the simulation includes quantum noise channels, the Aer simulator defaults to a **density matrix simulation method** which scales as $4^{\text{n\_qubits}}$. For SWAP tests, Aer simulates $2 \times \text{n\_qubits} + 1$ qubits (up to $17$ qubits at $\text{n\_qubits}=8$), which executes in milliseconds and fits comfortably within standard RAM.
* **Message & Copy Count (`message_bits` & `M`):** Keeping $\text{len}(\text{message\_bits}) \le 100$ and $M \le 10$ limits the total circuit count to $\le 1000$ verification circuits. Aer handles these in a single parallelized batch job, keeping runtime under 15 seconds.
* **Key Length & Precision (`L`):** Setting $L \ge 100$ guarantees the security margin $L > \text{n\_qubits} \times M$ is always positive (since max $\text{n\_qubits} \times M = 8 \times 10 = 80$). 

---

## 4. Key Relationships & Rules

* **Security Margin (Avoid Warning):**
  $$L > \text{n\_qubits} \times M$$
  *If $L - \text{n\_qubits} \times M \le 0$, the JSON output includes a warning about weak security parameters.*

* **Uniform Key Chunking (Recommended):**
  $$L \pmod{\text{n\_qubits}} = 0$$
  *Ensures even allocation of private key bits to qubits, avoiding angular resolution mismatch during public-key rotation.*

* **Threshold Consistency Constraint (Required):**
  $$0.0 < c1 < c2 < 1.0$$
  *Enforces that the acceptance threshold $c1$ is strictly smaller than the rejection threshold $c2$, and both lie within the open interval $(0, 1)$.*
