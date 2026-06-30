# QDS Input Range Guide


---

## 1. Parameter Specifications

| Parameter | Type | Hard Constraint | Recommended Range (Optimized for Aer Simulator) | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`message_bits`** | `str` | Non-empty, only `'0'`/`'1'` | Length $1$ to $100$ | Message to be signed |
| **`n_qubits`** | `int` | $1 \le \text{n\_qubits} \le L$ | $2$ to $8$ | Qubits per public key state |
| **`L`** | `int` | $L \ge \text{n\_qubits}$ | $100$ to $250$ | Bit-length of private keys |
| **`M`** | `int` | $M \ge 1$ | $3$ to $10$ | Public key copies per message bit |
| **`seed`** | `int` | Any integer | $0$ to $10^{6}$ | RNG & simulation seed |

>
> The recommended ranges above are chosen so that **any combination** of values within these bounds is guaranteed to satisfy all code validation rules and avoid the weak security warning ($L > n\_qubits \times M$).

---

## 2. Parameter Meanings

* **`message_bits`**: Binary message to sign.
* **`n_qubits`**: Qubits per quantum public key.
* **`L`**: Private key bit-length.
* **`M`**: Public key copies per receiver.
* **`seed`**: Random seed for reproducibility.

---

## 3. Aer Simulator Optimization Details

* **Qubit Count (`n_qubits`):** Keep $n\_qubits \le 8$. Since the simulation includes quantum noise channels, the Aer simulator defaults to a **density matrix simulation method** which scales as $4^{n\_qubits}$. For SWAP tests, Aer simulates $2 \times n\_qubits + 1$ qubits (up to $17$ qubits at $n\_qubits=8$), which executes in milliseconds and fits comfortably within standard RAM.
* **Message & Copy Count (`message_bits` & `M`):** Keeping $\text{len}(message\_bits) \le 100$ and $M \le 10$ limits the total circuit count to $\le 1000$ verification circuits. Aer handles these in a single parallelized batch job, keeping runtime under 15 seconds.
* **Key Length & Precision (`L`):** Setting $L \ge 100$ guarantees the security margin $L > n\_qubits \times M$ is always positive (since max $n\_qubits \times M = 8 \times 10 = 80$). 

---

## 4. Key Relationships

* **Security Margin (Avoid Warning):**
  $$L > n\_qubits \times M$$
  *If $L - n\_qubits \times M \le 0$, the class raises a warning about weak security parameters.*

* **Uniform Key Chunking:**
  $$L \pmod{n\_qubits} = 0$$
  *Ensures even allocation of private key bits to qubits, avoiding angular resolution mismatch during public-key rotation.*
