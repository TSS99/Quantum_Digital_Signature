"""Class-based Gottesman-Chuang style Quantum Digital Signature (QDS) protocol
with noisy quantum public-key transmission.

This module implements the key-distribution, honest-signing, and verification
stages of a Gottesman-Chuang style QDS scheme. Quantum noise is modeled only as
a transmission effect applied to the distributed public-key states, after ideal
state preparation and before verification.

The whole algorithm can be run end-to-end with a single call:

    result = QuantumDigitalSignatureWithChannelNoise(message_bits="101100").run()

or from the command line:

    python quantum_digital_signature_channel_noise.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import (
    amplitude_damping_error,
    depolarizing_error,
    pauli_error,
    phase_damping_error,
)


class QuantumDigitalSignatureWithChannelNoise:
    """Class-based Gottesman-Chuang style QDS protocol.

    The class stores ideal public-key circuits and received (post-channel)
    public-key circuits separately. Noise is inserted only by appending a
    quantum channel to each public-key qubit after ideal public-key preparation.
    """

    _ALLOWED_NOISE_CHANNELS = {
        "none",
        "depolarizing",
        "amplitude_damping",
        "phase_damping",
        "bit_flip",
        "phase_flip",
    }

    _ACCEPT_AUTHENTIC = "ACCEPT_AUTHENTIC"
    _REJECT_FORGED = "REJECT_FORGED"
    _INCONCLUSIVE = "INCONCLUSIVE"

    def __init__(
        self,
        message_bits: str,
        n_qubits: int = 4,
        L: int = 25,
        M: int = 5,
        c1: float = 0.1,
        c2: float = 0.4,
        shots: int = 4096,
        seed: int = 42,
        noise_channel: str = "none",
        noise_probability: float = 0.0,
        verification_pass_threshold: float = 0.80,
        verbose: bool = True,
    ):
        self._message_bits = message_bits
        self._n_qubits = n_qubits
        self._L = L
        self._M = M
        self._c1 = c1
        self._c2 = c2
        self._shots = shots
        self._seed = seed
        self._noise_channel = noise_channel.lower() if isinstance(noise_channel, str) else noise_channel
        self._noise_probability = noise_probability
        self._verification_pass_threshold = verification_pass_threshold
        self._verbose = verbose

        self._validate_inputs()

        self._n_qubits = int(self._n_qubits)
        self._L = int(self._L)
        self._M = int(self._M)
        self._shots = int(self._shots)
        self._seed = int(self._seed)
        self._c1 = float(self._c1)
        self._c2 = float(self._c2)
        self._noise_probability = float(self._noise_probability)
        self._verification_pass_threshold = float(self._verification_pass_threshold)

        self._security_margin = self._L - self._n_qubits * self._M
        self._rng = self._create_rng()
        self._simulator = AerSimulator(seed_simulator=self._seed)

        self._private_keys: Dict[int, List[Dict[int, str]]] = {}
        self._ideal_public_key_circuits: Dict[int, List[Dict[int, QuantumCircuit]]] = {}
        self._received_public_key_circuits: Dict[int, List[Dict[int, QuantumCircuit]]] = {}
        self._signature: Optional[Dict[str, Any]] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._warnings: List[str] = []

        if self._verbose:
            self._print_configuration()

        if self._security_margin <= 0:
            message = (
                "Weak security parameter choice: security_margin = "
                f"L - n_qubits*M = {self._security_margin}. "
                "Use a positive margin for a stronger Holevo-bound separation."
            )
            self._warnings.append(message)
            if self._verbose:
                self._print_json({
                    "event": "warning",
                    "warning": message,
                })

    # ------------------------------------------------------------------ #
    # Input validation
    # ------------------------------------------------------------------ #
    def _validate_inputs(self) -> None:
        if not isinstance(self._message_bits, str):
            raise TypeError("message_bits must be a string containing only '0' and '1'.")
        if len(self._message_bits) == 0:
            raise ValueError("message_bits must not be empty.")
        if any(bit not in "01" for bit in self._message_bits):
            raise ValueError("message_bits must contain only '0' and '1'.")

        self._validate_positive_integer(self._n_qubits, "n_qubits", minimum=1)
        self._validate_positive_integer(self._L, "L", minimum=1)
        self._validate_positive_integer(self._M, "M", minimum=1)
        self._validate_positive_integer(self._shots, "shots", minimum=1)

        if self._n_qubits > self._L:
            raise ValueError("n_qubits must not exceed L (each qubit needs at least one key bit).")

        if not isinstance(self._seed, (int, np.integer)) or isinstance(self._seed, bool):
            raise TypeError("seed must be an integer.")

        self._validate_numeric_probability(self._noise_probability, "noise_probability")
        self._validate_numeric_probability(self._verification_pass_threshold, "verification_pass_threshold")

        if self._noise_channel not in self._ALLOWED_NOISE_CHANNELS:
            allowed = ", ".join(sorted(self._ALLOWED_NOISE_CHANNELS))
            raise ValueError(f"noise_channel must be one of: {allowed}.")

        try:
            c1 = float(self._c1)
            c2 = float(self._c2)
        except (TypeError, ValueError) as exc:
            raise TypeError("c1 and c2 must be numeric values.") from exc

        if not (0.0 < c1 < c2 < 1.0):
            raise ValueError("Thresholds must satisfy 0 < c1 < c2 < 1.")

    def _validate_positive_integer(self, value: Any, name: str, minimum: int) -> None:
        if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer.")
        if int(value) < minimum:
            raise ValueError(f"{name} must be >= {minimum}.")

    def _validate_numeric_probability(self, value: Any, name: str) -> None:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{name} must be numeric.") from exc
        if not (0.0 <= numeric <= 1.0):
            raise ValueError(f"{name} must satisfy 0 <= {name} <= 1.")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _create_rng(self) -> np.random.Generator:
        return np.random.default_rng(self._seed)

    def _to_json(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, indent=2)

    def _print_json(self, payload: Dict[str, Any]) -> None:
        print(self._to_json(payload))

    def _compact_verification_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "message_bits": result["message_bits"],
            "verdict": result["verdict"],
            "failed_verifications": result["failed_verifications"],
            "total_verifications": result["total_verifications"],
            "failure_rate": result["failure_rate"],
            "authentic_threshold": result["authentic_threshold"],
            "reject_threshold": result["reject_threshold"],
            "security_margin": result["security_margin"],
            "noise_channel": result["noise_channel"],
            "noise_probability": result["noise_probability"],
            "warnings": result["warnings"],
            "generated_files": result.get("generated_files", {}),
            "decision_visualization": result.get("decision_visualization", {}),
        }

    def _configuration_payload(self) -> Dict[str, Any]:
        return {
            "message_bits": self._message_bits,
            "n_qubits": self._n_qubits,
            "L": self._L,
            "M": self._M,
            "c1": self._c1,
            "c2": self._c2,
            "shots": self._shots,
            "seed": self._seed,
            "noise_channel": self._noise_channel,
            "noise_probability": self._noise_probability,
            "verification_pass_threshold": self._verification_pass_threshold,
            "security_margin": self._security_margin,
            "warnings": list(self._warnings),
        }

    def _print_configuration(self) -> None:
        self._print_json({
            "event": "configuration",
            "configuration": self._configuration_payload(),
        })

    def _reset_protocol_state(self) -> None:
        self._rng = self._create_rng()
        self._private_keys = {}
        self._ideal_public_key_circuits = {}
        self._received_public_key_circuits = {}
        self._signature = None
        self._last_result = None

    def _random_key(self) -> str:
        bits = self._rng.integers(0, 2, size=self._L, dtype=np.int8)
        return "".join(str(int(bit)) for bit in bits)

    def _normalize_key(self, k: Any) -> str:
        if isinstance(k, str):
            key = k
        else:
            try:
                key = "".join(str(int(bit)) for bit in k)
            except TypeError as exc:
                raise TypeError("A private key must be a bit string or an iterable of bits.") from exc

        if len(key) != self._L:
            raise ValueError(f"Private key length must be exactly L={self._L}; received {len(key)}.")
        if any(bit not in "01" for bit in key):
            raise ValueError("Private keys must contain only '0' and '1'.")
        return key

    def _key_chunks(self, key: str) -> List[str]:
        base = self._L // self._n_qubits
        remainder = self._L % self._n_qubits
        chunks = []
        cursor = 0
        for qubit_index in range(self._n_qubits):
            chunk_length = base + (1 if qubit_index < remainder else 0)
            chunks.append(key[cursor: cursor + chunk_length])
            cursor += chunk_length
        return chunks

    def _rotation_angles_from_key(self, key: str) -> List[float]:
        angles = []
        for chunk in self._key_chunks(key):
            if len(chunk) == 0:
                angles.append(0.0)
                continue
            j_value = int(chunk, 2)
            theta_q = np.pi / float(2 ** len(chunk))
            angles.append(float(j_value) * theta_q)
        return angles

    # ------------------------------------------------------------------ #
    # Key generation
    # ------------------------------------------------------------------ #
    def _generate_private_keys(self) -> Dict[int, List[Dict[int, str]]]:
        # Reset the RNG so that key generation is reproducible regardless of
        # which public entry point triggered it (run, swap test, etc.).
        self._rng = self._create_rng()
        self._private_keys = {}
        for bit_index in range(len(self._message_bits)):
            self._private_keys[bit_index] = []
            for _ in range(self._M):
                self._private_keys[bit_index].append({
                    0: self._random_key(),
                    1: self._random_key(),
                })
        return self._private_keys

    def _build_public_key_state_circuit(self, k: Any) -> QuantumCircuit:
        """Build only the ideal noiseless state-preparation circuit for |f_k>."""
        key = self._normalize_key(k)
        circuit = QuantumCircuit(self._n_qubits, name="ideal_public_key")
        for qubit_index, angle in enumerate(self._rotation_angles_from_key(key)):
            if not np.isclose(angle, 0.0):
                circuit.ry(2.0 * angle, qubit_index)
        return circuit

    # ------------------------------------------------------------------ #
    # Channel noise
    # ------------------------------------------------------------------ #
    def _channel_error_instruction(self):
        p = self._noise_probability
        if self._noise_channel == "depolarizing":
            return depolarizing_error(p, 1).to_instruction()
        if self._noise_channel == "amplitude_damping":
            return amplitude_damping_error(p).to_instruction()
        if self._noise_channel == "phase_damping":
            return phase_damping_error(p).to_instruction()
        if self._noise_channel == "bit_flip":
            return pauli_error([("X", p), ("I", 1.0 - p)]).to_instruction()
        if self._noise_channel == "phase_flip":
            return pauli_error([("Z", p), ("I", 1.0 - p)]).to_instruction()
        raise ValueError(f"No quantum error instruction is defined for channel {self._noise_channel!r}.")

    def _apply_quantum_channel_noise(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """Copy an ideal public-key circuit and append channel noise to each qubit."""
        transmitted = circuit.copy()
        transmitted.name = "received_public_key"

        if self._noise_channel == "none" or np.isclose(self._noise_probability, 0.0):
            return transmitted

        error_instruction = self._channel_error_instruction()
        for qubit_index in range(self._n_qubits):
            transmitted.append(error_instruction, [qubit_index])
        return transmitted

    def _transmit_public_key_through_channel(self, ideal_circuit: QuantumCircuit) -> QuantumCircuit:
        return self._apply_quantum_channel_noise(ideal_circuit)

    def _generate_public_keys(self) -> Tuple[
        Dict[int, List[Dict[int, QuantumCircuit]]],
        Dict[int, List[Dict[int, QuantumCircuit]]],
    ]:
        if not self._private_keys:
            self._generate_private_keys()

        self._ideal_public_key_circuits = {}
        self._received_public_key_circuits = {}

        for bit_index, key_copies in self._private_keys.items():
            self._ideal_public_key_circuits[bit_index] = []
            self._received_public_key_circuits[bit_index] = []

            for key_pair in key_copies:
                ideal_pair = {}
                received_pair = {}
                for bit_value in (0, 1):
                    ideal_circuit = self._build_public_key_state_circuit(key_pair[bit_value])
                    received_circuit = self._transmit_public_key_through_channel(ideal_circuit)
                    ideal_pair[bit_value] = ideal_circuit
                    received_pair[bit_value] = received_circuit
                self._ideal_public_key_circuits[bit_index].append(ideal_pair)
                self._received_public_key_circuits[bit_index].append(received_pair)

        return self._ideal_public_key_circuits, self._received_public_key_circuits

    def _build_inverse_verification_circuit(self, k: Any) -> QuantumCircuit:
        """Build the ideal inverse circuit from a revealed classical private key."""
        return self._build_public_key_state_circuit(k).inverse()

    # ------------------------------------------------------------------ #
    # Signing
    # ------------------------------------------------------------------ #
    def _generate_signature(self) -> Dict[str, Any]:
        """Honest signature: reveal the correct private keys for each message bit."""
        if not self._private_keys:
            raise RuntimeError("Generate private keys before signing. Use run() or _generate_private_keys().")

        revealed: Dict[int, Dict[str, Any]] = {}
        for bit_index, bit_char in enumerate(self._message_bits):
            bit_value = int(bit_char)
            revealed[bit_index] = {
                "bit_value": bit_value,
                "keys": [self._private_keys[bit_index][copy_index][bit_value] for copy_index in range(self._M)],
            }

        self._signature = {
            "message_bits": self._message_bits,
            "revealed_keys": revealed,
        }
        return self._signature

    def _forge_signature(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Adversarial signature: a forger who does not know the private keys
        guesses random keys of the correct length. This is used to exercise the
        REJECT_FORGED decision branch.
        """
        forger_rng = np.random.default_rng(self._seed + 1 if seed is None else seed)

        def _random_forged_key() -> str:
            bits = forger_rng.integers(0, 2, size=self._L, dtype=np.int8)
            return "".join(str(int(bit)) for bit in bits)

        revealed: Dict[int, Dict[str, Any]] = {}
        for bit_index, bit_char in enumerate(self._message_bits):
            bit_value = int(bit_char)
            revealed[bit_index] = {
                "bit_value": bit_value,
                "keys": [_random_forged_key() for _ in range(self._M)],
            }

        return {
            "message_bits": self._message_bits,
            "revealed_keys": revealed,
        }

    # ------------------------------------------------------------------ #
    # Verification
    # ------------------------------------------------------------------ #
    def _verification_circuit(self, received_public_key_circuit: QuantumCircuit, revealed_key: str) -> QuantumCircuit:
        inverse_circuit = self._build_inverse_verification_circuit(revealed_key)
        circuit = QuantumCircuit(self._n_qubits, self._n_qubits, name="verify_received_public_key")
        circuit.compose(received_public_key_circuit, qubits=list(range(self._n_qubits)), inplace=True)
        circuit.compose(inverse_circuit, qubits=list(range(self._n_qubits)), inplace=True)
        circuit.measure(list(range(self._n_qubits)), list(range(self._n_qubits)))
        return circuit

    def _verify_signature(self, signature: Dict[str, Any]) -> Dict[str, Any]:
        if not self._received_public_key_circuits:
            raise RuntimeError("Received public keys are not available. Generate and transmit public keys first.")

        message = signature.get("message_bits")
        revealed_keys = signature.get("revealed_keys")
        if message != self._message_bits:
            raise ValueError("Signature message does not match this verifier's public-key allocation.")
        if not isinstance(revealed_keys, dict):
            raise ValueError("Signature must contain a revealed_keys dictionary.")

        verification_circuits = []
        metadata = []
        for bit_index, bit_char in enumerate(message):
            bit_value = int(bit_char)
            bit_signature = revealed_keys.get(bit_index)
            if bit_signature is None:
                raise ValueError(f"Signature is missing bit index {bit_index}.")
            if int(bit_signature.get("bit_value")) != bit_value:
                raise ValueError(f"Signature bit value mismatch at bit index {bit_index}.")
            keys = bit_signature.get("keys")
            if not isinstance(keys, Sequence) or len(keys) != self._M:
                raise ValueError(f"Signature bit index {bit_index} must contain exactly M={self._M} keys.")

            for copy_index, revealed_key in enumerate(keys):
                normalized_key = self._normalize_key(revealed_key)
                received_public_key = self._received_public_key_circuits[bit_index][copy_index][bit_value]
                verification_circuits.append(self._verification_circuit(received_public_key, normalized_key))
                metadata.append({
                    "bit_index": bit_index,
                    "bit_value": bit_value,
                    "copy_index": copy_index,
                })

        transpiled = transpile(verification_circuits, self._simulator, seed_transpiler=self._seed)
        job = self._simulator.run(transpiled, shots=self._shots)
        result = job.result()

        zero_state = "0" * self._n_qubits
        failed_verifications = 0
        per_bit_results: Dict[int, Dict[str, Any]] = {}
        raw_counts_summary = []

        for circuit_index, item in enumerate(metadata):
            counts = dict(result.get_counts(circuit_index))
            zero_probability = counts.get(zero_state, 0) / float(self._shots)
            passed = bool(zero_probability >= self._verification_pass_threshold)
            if not passed:
                failed_verifications += 1

            bit_index = str(item["bit_index"])
            if bit_index not in per_bit_results:
                per_bit_results[bit_index] = {
                    "bit_value": item["bit_value"],
                    "failed_verifications": 0,
                    "copy_results": [],
                }
            if not passed:
                per_bit_results[bit_index]["failed_verifications"] += 1

            copy_result = {
                "copy_index": item["copy_index"],
                "zero_state_probability": zero_probability,
                "passed": passed,
                "counts": counts,
            }
            per_bit_results[bit_index]["copy_results"].append(copy_result)
            raw_counts_summary.append({
                "bit_index": bit_index,
                "bit_value": item["bit_value"],
                "copy_index": item["copy_index"],
                "counts": counts,
            })

        total_verifications = len(message) * self._M
        authentic_threshold = self._c1 * total_verifications
        reject_threshold = self._c2 * total_verifications
        failure_rate = failed_verifications / float(total_verifications)

        if failed_verifications <= authentic_threshold:
            verdict = self._ACCEPT_AUTHENTIC
        elif failed_verifications >= reject_threshold:
            verdict = self._REJECT_FORGED
        else:
            verdict = self._INCONCLUSIVE

        for bit_index, bit_result in per_bit_results.items():
            bit_result["failure_rate"] = bit_result["failed_verifications"] / float(self._M)

        verification_result = {
            "message_bits": message,
            "n_qubits": self._n_qubits,
            "L": self._L,
            "M": self._M,
            "c1": self._c1,
            "c2": self._c2,
            "shots": self._shots,
            "seed": self._seed,
            "noise_channel": self._noise_channel,
            "noise_probability": self._noise_probability,
            "security_margin": self._security_margin,
            "warnings": list(self._warnings),
            "total_verifications": total_verifications,
            "failed_verifications": failed_verifications,
            "failure_rate": failure_rate,
            "authentic_threshold": authentic_threshold,
            "reject_threshold": reject_threshold,
            "verdict": verdict,
            "per_bit_results": per_bit_results,
            "raw_counts_summary": raw_counts_summary,
        }
        self._last_result = verification_result
        return verification_result

    def _decision_visualization_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        total = int(result["total_verifications"])
        authentic_threshold = float(result["authentic_threshold"])
        reject_threshold = float(result["reject_threshold"])
        failed = int(result["failed_verifications"])
        return {
            "zones": {
                "green": {
                    "label": "ACCEPT_AUTHENTIC",
                    "range": [0, authentic_threshold],
                    "colour": "#e6f4ea",
                },
                "yellow": {
                    "label": "INCONCLUSIVE",
                    "range": [authentic_threshold, reject_threshold],
                    "colour": "#fef7e0",
                },
                "red": {
                    "label": "REJECT_FORGED",
                    "range": [reject_threshold, total],
                    "colour": "#fce8e6",
                },
            },
            "thresholds": [
                {
                    "label": "c1*T",
                    "location": authentic_threshold,
                    "colour": "#16a34a",
                },
                {
                    "label": "c2*T",
                    "location": reject_threshold,
                    "colour": "#dc2626",
                },
            ],
            "points": [
                {
                    "label": "observed_failures",
                    "location": [failed, 0.15],
                    "colour": "#2563eb",
                    "verdict": result["verdict"],
                },
            ],
            "axes": {
                "x": {
                    "label": "Failed verification checks",
                    "range": [0, total],
                },
                "y": {
                    "label": "Decision marker height",
                    "range": [0, 1],
                },
            },
        }

    def _generate_verification_decision_image(
        self,
        result: Dict[str, Any],
        output_path: str = "verification_decision.png",
    ) -> str:
        visualization = self._decision_visualization_payload(result)
        total = int(result["total_verifications"])
        authentic_threshold = float(result["authentic_threshold"])
        reject_threshold = float(result["reject_threshold"])
        failed = int(result["failed_verifications"])
        zones = visualization["zones"]
        observed_point = visualization["points"][0]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')

        # Draw decision zones
        ax.axvspan(-0.5, authentic_threshold, color=zones["green"]["colour"], alpha=0.9, label=zones["green"]["label"])
        ax.axvspan(authentic_threshold, reject_threshold, color=zones["yellow"]["colour"], alpha=0.9, label=zones["yellow"]["label"])
        ax.axvspan(reject_threshold, total + 0.5, color=zones["red"]["colour"], alpha=0.9, label=zones["red"]["label"])

        # Draw threshold lines
        ax.axvline(authentic_threshold, color=visualization["thresholds"][0]["colour"], linestyle="--", linewidth=1.5, alpha=0.8)
        ax.axvline(reject_threshold, color=visualization["thresholds"][1]["colour"], linestyle="--", linewidth=1.5, alpha=0.8)

        # Draw observed failures marker as a glowing pin
        ax.vlines(failed, 0, 0.55, color='#93c5fd', linewidth=6, alpha=0.4, zorder=3)
        ax.vlines(failed, 0, 0.55, color=observed_point["colour"], linewidth=2.5, zorder=4)
        ax.scatter(failed, 0.55, color='#93c5fd', s=180, alpha=0.4, zorder=4)
        ax.scatter(failed, 0.55, color=observed_point["colour"], s=90, zorder=5, edgecolor='#ffffff', linewidth=1.5)

        # Add tooltip-like annotation for observed failures
        ax.annotate(
            f"{result['verdict']}\n({failed} failures)",
            xy=(failed, 0.55),
            xytext=(0, 15),
            textcoords="offset points",
            ha='center',
            va='bottom',
            color='#ffffff',
            fontweight='bold',
            fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.6", fc='#0f172a', ec=observed_point["colour"], lw=1.5),
            zorder=6
        )

        ax.set_xlim(-0.5, total + 0.5)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        
        # Remove spines
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.spines["bottom"].set_linewidth(1.5)

        ax.tick_params(axis='x', colors='#475569', labelsize=9.5)
        ax.set_xlabel("Failed verification checks", fontsize=10.5, fontweight="semibold", color="#334155", labelpad=12)
        ax.set_title("Quantum Digital Signature Verification Decision", fontsize=13, fontweight="bold", color="#0f172a", pad=20)

        # Threshold text labels using LaTeX mathtext
        ax.text(
            authentic_threshold - 0.25,
            0.88,
            r"$c_1 \cdot T = " + f"{authentic_threshold:.1f}$",
            ha="right",
            va="center",
            color=visualization["thresholds"][0]["colour"],
            fontweight="bold",
            fontsize=10
        )
        ax.text(
            reject_threshold + 0.25,
            0.88,
            r"$c_2 \cdot T = " + f"{reject_threshold:.1f}$",
            ha="left",
            va="center",
            color=visualization["thresholds"][1]["colour"],
            fontweight="bold",
            fontsize=10
        )

        # Custom legend patches
        import matplotlib.patches as mpatches
        green_patch = mpatches.Patch(color=zones["green"]["colour"], alpha=0.9, label=zones["green"]["label"])
        yellow_patch = mpatches.Patch(color=zones["yellow"]["colour"], alpha=0.9, label=zones["yellow"]["label"])
        red_patch = mpatches.Patch(color=zones["red"]["colour"], alpha=0.9, label=zones["red"]["label"])
        
        ax.legend(
            handles=[green_patch, yellow_patch, red_patch],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.2),
            ncol=3,
            frameon=True,
            facecolor='#ffffff',
            edgecolor='#e2e8f0',
            fontsize=9.5,
            labelcolor='#475569'
        )
        fig.tight_layout()

        destination = Path(output_path)
        fig.savefig(destination, dpi=160, bbox_inches="tight")
        plt.close(fig)
        return str(destination)

    # ------------------------------------------------------------------ #
    # Single end-to-end entry point
    # ------------------------------------------------------------------ #
    def run(self) -> str:
        """Run the full honest QDS workflow end-to-end and return JSON output."""
        self._reset_protocol_state()
        self._generate_private_keys()
        self._generate_public_keys()
        signature = self._generate_signature()
        result = self._verify_signature(signature)
        result["decision_visualization"] = self._decision_visualization_payload(result)
        result["generated_files"] = {
            "verification_decision": self._generate_verification_decision_image(result),
        }
        self._last_result = result
        if self._verbose:
            self._summarize_results(result)
        return self._to_json(self._compact_verification_result(result))

    def run_forgery_attempt(self) -> str:
        """Run the protocol but verify against a forged (random-key) signature.

        Demonstrates the REJECT_FORGED branch under honest channel conditions.
        """
        self._reset_protocol_state()
        self._generate_private_keys()
        self._generate_public_keys()
        forged = self._forge_signature()
        result = self._verify_signature(forged)
        result["decision_visualization"] = self._decision_visualization_payload(result)
        result["generated_files"] = {
            "verification_decision": self._generate_verification_decision_image(result),
        }
        self._last_result = result
        if self._verbose:
            self._summarize_results(result)
        return self._to_json(self._compact_verification_result(result))

    def _summarize_results(self, result: Optional[Dict[str, Any]] = None) -> None:
        data = self._last_result if result is None else result
        if data is None:
            self._print_json({
                "event": "result",
                "error": "No protocol result is available yet.",
            })
            return
        self._print_json({
            "event": "result",
            "result": self._compact_verification_result(data),
        })

    # ------------------------------------------------------------------ #
    # Optional diagnostics
    # ------------------------------------------------------------------ #
    def _swap_test(self, circuit_a: QuantumCircuit, circuit_b: QuantumCircuit) -> Dict[str, Any]:
        if circuit_a.num_qubits != self._n_qubits or circuit_b.num_qubits != self._n_qubits:
            raise ValueError("SWAP-test inputs must both act on n_qubits qubits.")

        total_qubits = 2 * self._n_qubits + 1
        swap_circuit = QuantumCircuit(total_qubits, 1, name="swap_test")
        ancilla = 0
        register_a = list(range(1, self._n_qubits + 1))
        register_b = list(range(self._n_qubits + 1, 2 * self._n_qubits + 1))

        swap_circuit.h(ancilla)
        swap_circuit.compose(circuit_a, qubits=register_a, inplace=True)
        swap_circuit.compose(circuit_b, qubits=register_b, inplace=True)
        for offset in range(self._n_qubits):
            swap_circuit.cswap(ancilla, register_a[offset], register_b[offset])
        swap_circuit.h(ancilla)
        swap_circuit.measure(ancilla, 0)

        transpiled = transpile(swap_circuit, self._simulator, seed_transpiler=self._seed)
        result = self._simulator.run(transpiled, shots=self._shots).result()
        counts = dict(result.get_counts())
        p_zero = counts.get("0", 0) / float(self._shots)
        return {
            "p_ancilla_zero": p_zero,
            "counts": counts,
            "circuit": {
                "name": swap_circuit.name,
                "num_qubits": swap_circuit.num_qubits,
                "num_clbits": swap_circuit.num_clbits,
                "depth": swap_circuit.depth(),
                "operation_counts": dict(swap_circuit.count_ops()),
            },
        }

    def _compact_swap_test_result(self, result: Dict[str, Any], include_plot: bool) -> Dict[str, Any]:
        compact = {
            "bit_index": result["bit_index"],
            "copy_index": result["copy_index"],
            "bit_value": result["bit_value"],
            "comparisons": {
                label: {
                    "p_ancilla_zero": comparison["p_ancilla_zero"],
                }
                for label, comparison in result["comparisons"].items()
            },
        }
        if include_plot:
            compact["plot"] = {
                "type": "bar",
                "title": "SWAP Test Public-Key State Comparisons",
                "x_label": "comparison",
                "y_label": "P(ancilla = 0)",
                "y_range": [0.45, 1.02],
                "series": [
                    {
                        "label": label,
                        "value": data["p_ancilla_zero"],
                    }
                    for label, data in compact["comparisons"].items()
                ],
            }
        return compact

    def run_swap_test_example(
        self,
        bit_index: int = 0,
        copy_index: int = 0,
        bit_value: Optional[int] = None,
        make_plot: bool = True,
    ) -> str:
        if not self._received_public_key_circuits:
            self._generate_public_keys()

        if not (0 <= bit_index < len(self._message_bits)):
            raise ValueError("bit_index is out of range.")
        if not (0 <= copy_index < self._M):
            raise ValueError("copy_index is out of range.")

        selected_bit_value = int(self._message_bits[bit_index]) if bit_value is None else int(bit_value)
        if selected_bit_value not in (0, 1):
            raise ValueError("bit_value must be 0 or 1.")

        ideal = self._ideal_public_key_circuits[bit_index][copy_index][selected_bit_value]
        received = self._received_public_key_circuits[bit_index][copy_index][selected_bit_value]
        complementary_ideal = self._ideal_public_key_circuits[bit_index][copy_index][1 - selected_bit_value]

        comparisons = {
            "ideal_vs_ideal": self._swap_test(ideal, ideal),
            "ideal_vs_received": self._swap_test(ideal, received),
            "ideal_vs_complementary": self._swap_test(ideal, complementary_ideal),
        }

        detailed_payload = {
            "bit_index": bit_index,
            "copy_index": copy_index,
            "bit_value": selected_bit_value,
            "comparisons": comparisons,
        }
        return self._to_json(self._compact_swap_test_result(detailed_payload, make_plot))

    def _plot_noise_sweep(
        self,
        p_values: Sequence[float],
        noise_channel: str = "depolarizing",
        figure_size: Tuple[float, float] = (7.5, 4.5),
    ) -> str:
        if noise_channel not in self._ALLOWED_NOISE_CHANNELS:
            allowed = ", ".join(sorted(self._ALLOWED_NOISE_CHANNELS))
            raise ValueError(f"noise_channel must be one of: {allowed}.")

        sweep_results = []
        for p in p_values:
            self._validate_numeric_probability(p, "p")
            trial = self.__class__(
                message_bits=self._message_bits,
                n_qubits=self._n_qubits,
                L=self._L,
                M=self._M,
                c1=self._c1,
                c2=self._c2,
                shots=self._shots,
                seed=self._seed,
                noise_channel=noise_channel,
                noise_probability=float(p),
                verification_pass_threshold=self._verification_pass_threshold,
                verbose=False,
            )
            sweep_results.append(json.loads(trial.run()))

        probabilities = [item["noise_probability"] for item in sweep_results]
        failure_rates = [item["failure_rate"] for item in sweep_results]

        return self._to_json({
            "noise_channel": noise_channel,
            "figure_size": list(figure_size),
            "sweep_results": sweep_results,
            "plot": {
                "type": "line",
                "title": f"{noise_channel.replace('_', ' ').title()} Noise Sweep",
                "x_label": "Noise probability",
                "y_label": "Failure rate",
                "y_range": [-0.02, 1.02],
                "series": [
                    {
                        "label": "failure_rate",
                        "x": probabilities,
                        "y": failure_rates,
                        "color": "#1565c0",
                    }
                ],
                "thresholds": [
                    {
                        "label": f"authentic threshold c1={self._c1}",
                        "value": self._c1,
                        "color": "#2e7d32",
                    },
                    {
                        "label": f"reject threshold c2={self._c2}",
                        "value": self._c2,
                        "color": "#c62828",
                    },
                ],
            },
        })


def _main() -> None:
    """Single entry point: run the full QDS protocol once and print the verdict."""
    try:
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
            verbose=False,
        )
        print(qds.run())
    except Exception as exc:
        print(json.dumps({
            "event": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    _main()
