# Quantum Digital Signatures

Digital signatures are among the most widely deployed cryptographic primitives in modern computing. Every signed software
update, TLS handshake, and authenticated email leans on the same promise: a
message came from who it claims to, and arrived as it was sent. This
explains how that promise can be rebuilt on quantum mechanics instead of
computational hardness, and walks through the small protocol implemented in this
repository. It assumes no quantum background â€” only some patience with the fact
that measurement and copying behave differently at the scale of single qubits.

## What a signature has to guarantee

Three properties matter here, and conflating them hides the interesting part.

Authenticity is identity: the recipient can confirm the message came from the
claimed signer and no one else. Integrity is tamper-evidence: any change after
signing is detectable. Both are what people usually picture when they hear
"signature," and both are relatively easy to reason about.

The third property, **non-repudiation**, is subtler, and it is where signatures
earn their legal and commercial weight. Non-repudiation means the signer cannot
later deny having signed. A signature on a contract is valuable precisely because
the signer cannot credibly claim someone else produced it. The catch is that in a
distributed setting this becomes a *consistency* requirement rather than a
property of any single check: two recipients who each verify the same signed
message must reach the same verdict. If Alice could craft something that Bob
accepts but Charlie rejects, she could honor or disown it at will, and the
signature would mean nothing in a dispute. Non-repudiation therefore lives in the
agreement between verifiers, not inside one verification. This distinction quietly
shapes the verdict rule described later, and it is also the hardest of the three
to provide â€” the original Gottesmanâ€“Chuang protocol spends most of its machinery
on it.

## Why the classical foundation is at risk

RSA-style signatures derive all three properties from a single assumption: that
recovering the private key from the public key means solving a problem â€”
factoring, or discrete logarithms â€” that no feasible computer cracks quickly. The
assumption has held in practice, but it is a claim about which algorithms exist
and what hardware can run them, not a law of nature.

Shor's algorithm withdraws that safety against a quantum adversary. A large
fault-tolerant quantum computer factors integers and computes discrete logarithms
in polynomial time, collapsing the distance between producing a signature and
forging one. The threat is narrow and specific: it attacks the hardness
assumption, leaving the protocol logic untouched. That specificity is the whole
motivation for a different foundation â€” one where forging stays out of reach even
for an adversary with unbounded computation.

## Security from physics rather than hardness

Gottesman and Chuang's 2001 proposal trades the computational assumption for two
physical facts no amount of computing power can route around.

The first is no-cloning: an unknown quantum state cannot be copied. The second is
that measurement is both destructive and incomplete â€” pulling classical
information out of a quantum state disturbs it and never reveals everything. A
quantum public key, then, cannot be quietly duplicated, taken offline, and
reverse-engineered the way a classical public key can.

The **Holevo bound** turns these qualitative facts into a usable number: a
measurement on `n` qubits yields at most `n` bits of classical information, no
matter how the measurement is designed. That ceiling is the lever the whole scheme
pulls. If Alice's private key carries substantially more entropy than her quantum
public key can possibly leak, then no measurement an adversary performs â€” now or
years later, with any machine â€” recovers the key. Security stops scaling with the
attacker's resources and starts resting on an information inequality.

## The construction, step by step

The implementation runs on Qiskit's Aer simulator with a default configuration
worth holding in mind: a six-bit message `101100`, each public key encoded across
`n = 4` qubits, private keys of length `L = 25` bits, and `M = 5` independent
copies distributed per message bit. Everything below describes a single message
bit; the full message simply repeats the procedure bit by bit.

**Key generation.** For each message bit Alice draws two independent random
`L`-bit strings, one earmarked for signing the value `0` and the other for `1`,
and she repeats this `M` times to get `M` copies. The private key is nothing more
than these random strings. Their secrecy is the entire basis of her later claim to
authorship.

**Encoding into states.** A private key is read as an integer `j` and mapped to a
rotation angle. With

$$\theta = \frac{\pi}{2^{L}}, \qquad \varphi = j\,\theta,$$

a qubit prepared from `|0âŸ©` by an `RY(2Ï†)` rotation lands in

$$|f_k\rangle = \cos(\varphi)\,|0\rangle + \sin(\varphi)\,|1\rangle.$$

Computing this state from the key is trivial; inverting it from the state alone is
blocked by the readout limits above, which is exactly the one-way behavior the
protocol needs. The code splits the `L`-bit key into one chunk per qubit so the
angular resolution stays manageable, but each chunk obeys the same rule. Choosing
`RY` â€” a real rotation in the `|0âŸ©`â€“`|1âŸ©` plane â€” keeps the states real and makes
the inverse a clean negation of the angle, which pays off at verification.

**Distribution through a noisy channel.** Alice transmits the public-key states,
and the implementation models the imperfection of that transmission directly. A
configurable channel â€” depolarizing, bit-flip, phase-flip, amplitude damping, or
phase damping â€” acts on each qubit with strength `p` before the verifier stores
it. Noise is confined to this step by design; preparation, signing, and
verification remain ideal. The aim is to read off what the channel alone does to
the protocol's success rate, without tangling it up with gate or measurement
error. The isolation is artificial â€” real hardware is noisy everywhere â€” but it
makes the channel's contribution legible, which is the point of a study model.

**Signing.** Alice signs by announcing the private keys themselves. Disclosing the
correct `L`-bit strings for the bits she is committing to *is* the signature;
there is no separate signing transform. This is what binds authorship to secrecy:
only the holder of the original random keys can produce them on demand.

**Verification.** Holding the stored public-key state, the verifier reconstructs
the rotation implied by a revealed key and applies its inverse. For a genuine key
on a clean channel the inverse returns the qubit to `|0âŸ©` exactly, so measuring all
qubits should read all-zeros. Since measurement is probabilistic and the channel is
not clean, the verifier does not insist on one perfect shot; it estimates the
all-zeros probability over many shots and counts a check as passing when

$$P(\text{all zeros}) \ge \tau,$$

with `Ï„ = 0.80` in the code. Across every bit and copy this produces `T = N Ã— M`
checks â€” `30` under the defaults.

## Turning checks into a verdict

The non-repudiation requirement re-enters here. Let `s` be the number of failed
checks out of `T`. Rather than a single cut-off, the verifier uses two:

$$\begin{aligned}
s \le c_1 T &\;\Rightarrow\; \texttt{ACCEPT\_AUTHENTIC} \\
s \ge c_2 T &\;\Rightarrow\; \texttt{REJECT\_FORGED} \\
c_1 T < s < c_2 T &\;\Rightarrow\; \texttt{INCONCLUSIVE}
\end{aligned}$$

with defaults `c1 = 0.1` and `c2 = 0.4`, i.e. cut-offs at `3` and `12` failures.

The band between the thresholds is not hedging. A lone threshold would force a
ruling on borderline evidence, and borderline cases are exactly where two honest
verifiers, exposed to slightly different noise, might split â€” the one outcome
non-repudiation cannot tolerate. The gap soaks up that ambiguity: real signatures
clear the lower bound with room to spare, forgeries sail past the upper one, and
the uneasy middle is labeled inconclusive instead of being resolved
inconsistently. In the full transferable protocol the original recipient and a
forwarded recipient sit at different points inside this gap, and the separation
`c2 âˆ’ c1` is precisely what keeps a message one accepts from being a message the
other rejects.

## Why forgery fails

A forger has no access to the private keys and can only guess. A wrong guess
rebuilds the wrong rotation, so the inverse fails to restore `|0âŸ©`. For a single
qubit, with true angle `Ï†` and guessed angle `Ï†Ìƒ`, the all-zeros probability is

$$P(\text{all zeros}) = \cos^2(\varphi - \tilde{\varphi}),$$

which falls well under `Ï„` unless the guess is almost exact. Guessing a 25-bit key
outright carries probability `2â»Â²âµ`, about one in 34 million. The bundled forgery
routine shows the inevitable result: all 30 checks fail and the verdict is
`REJECT_FORGED`. The same expression explains the protocol's tolerance for mild
noise â€” a small perturbation nudges `P(all zeros)` down slightly, but it takes
serious corruption to drag a genuine check below `0.80`.

## Reading the security margin

The code prints a diagnostic it calls the security margin,

$$\text{security margin} = L - nM,$$

setting the entropy Alice holds (`L` bits) against a generous estimate of what the
public copies can leak (`n` qubits per copy, so at most `nM` bits by the Holevo
bound). The defaults give `25 âˆ’ 20 = 5`. A positive value means the secret
outweighs the leak and the protocol sits in its intended regime; the code still
runs at zero or negative margins but warns, since there the Holevo separation no
longer shields the key. Read this as a design heuristic, not a proof â€” it flags
bad parameter choices without certifying good ones.

## Scope and limitations

It helps to be precise about what this code is. It is a simulator-based teaching
implementation of the verification core: key encoding, noisy distribution, signing
by disclosure, and threshold verification. It is not a deployable cryptosystem,
and it does not build the full multi-recipient transfer protocol that genuine
non-repudiation demands. The two-threshold rule that would underpin transferability
is present and working, but with a single verifier the consistency-across-recipients
guarantee is shown in mechanism rather than enforced end to end. Because noise is
modeled only on the channel, the results speak to transmission robustness, not to
full hardware fidelity.

## Public API and usage

The class exposes a deliberately small public API. Construct an instance with the
protocol parameters, then call one of these public methods:

- `run()` for an honest end-to-end signing and verification run.
- `run_forgery_attempt()` for the adversarial random-key forgery example.
- `run_swap_test_example()` for a SWAP-test comparison of public-key states.

All other methods, constants, and stored state are implementation details and are
private underscore-prefixed members. Use the dictionaries returned by the public
methods instead of reading internal attributes.

### Constructor parameters

```python
from quantum_digital_signature_channel_noise import QuantumDigitalSignatureWithChannelNoise

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
    verification_pass_threshold=0.80,
    verbose=True,
)
```

| Parameter | Meaning |
|-----------|---------|
| `message_bits` | Binary message string to sign, for example `"101100"`. Each character must be `0` or `1`. |
| `n_qubits` | Number of qubits used to encode each public-key state. Must be at least `1` and not greater than `L`. |
| `L` | Number of bits in each private key. Larger values increase the private-key search space. |
| `M` | Number of independent public-key copies per message bit. Total checks are `len(message_bits) * M`. |
| `c1` | Authentic acceptance fraction. The result is accepted when failed checks are `<= c1 * total_verifications`. |
| `c2` | Forgery rejection fraction. The result is rejected when failed checks are `>= c2 * total_verifications`. Must satisfy `0 < c1 < c2 < 1`. |
| `shots` | Number of simulator measurement repetitions per verification circuit. |
| `seed` | Integer seed for deterministic private-key generation and simulator transpilation. |
| `noise_channel` | Channel applied during public-key transmission: `none`, `depolarizing`, `amplitude_damping`, `phase_damping`, `bit_flip`, or `phase_flip`. |
| `noise_probability` | Channel strength in `[0.0, 1.0]`. Use `0.0` for a clean channel. |
| `verification_pass_threshold` | Minimum all-zero probability required for a single verification check to pass. |
| `verbose` | When `True`, prints configuration and run summaries. When `False`, only return dictionaries are produced. |

### `run()`

```python
result = qds.run()
```

Runs the honest protocol: reset state, generate private keys, build and transmit
public-key states, reveal the correct private keys as the signature, verify the
signature, and return a result dictionary. It takes no method parameters; all
inputs come from the constructor.

Important result fields include `verdict`, `failed_verifications`,
`failure_rate`, `total_verifications`, `per_bit_results`, and
`raw_counts_summary`.

### `run_forgery_attempt()`

```python
forgery_result = qds.run_forgery_attempt()
```

Runs the same setup as `run()`, but verifies a forged signature made from random
private-key guesses. It takes no method parameters and returns the same result
dictionary shape as `run()`. Under clean default conditions the expected verdict
is `REJECT_FORGED`.

### `run_swap_test_example(...)`

```python
swap_result = qds.run_swap_test_example(
    bit_index=0,
    copy_index=0,
    bit_value=None,
    make_plot=True,
)
```

Runs three SWAP-test comparisons for one selected public-key state:
`ideal_vs_ideal`, `ideal_vs_received`, and `ideal_vs_complementary`.

| Parameter | Meaning |
|-----------|---------|
| `bit_index` | Message-bit position to inspect. Valid range is `0 <= bit_index < len(message_bits)`. |
| `copy_index` | Public-key copy number for that bit. Valid range is `0 <= copy_index < M`. |
| `bit_value` | Which key state to compare, `0` or `1`. If `None`, the actual message bit at `bit_index` is used. |
| `make_plot` | When `True`, displays a Matplotlib bar chart of the SWAP-test probabilities. |

The returned dictionary includes the selected indices and a `comparisons` mapping.
Each comparison contains `p_ancilla_zero`, raw `counts`, and the generated
`QuantumCircuit`.


