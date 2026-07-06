"""Test cases for QuantumDigitalSignatureWithChannelNoise.

These tests use the Python standard-library `unittest` framework, so no extra
dependency (pytest) is required. Run with either:

    python -m unittest test_quantum_digital_signature -v
    python test_quantum_digital_signature.py

Note: each verification run launches the Aer simulator, so the full suite takes
a little time. Lightweight parameters (small L, M, shots) are used where the
quantum result is not the point of the test.
"""

import unittest
import warnings
import inspect
import json
from pathlib import Path

import numpy as np

from quantum_digital_signature_channel_noise import (
    QuantumDigitalSignatureWithChannelNoise as QDS,
)


def as_json(payload):
    return json.loads(payload)


# --------------------------------------------------------------------------- #
# 1. Honest workflow
# --------------------------------------------------------------------------- #
class TestHonestWorkflow(unittest.TestCase):
    def test_public_api_is_intentionally_small(self):
        public_methods = {
            name
            for name, value in inspect.getmembers(QDS, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        public_data = {
            name
            for name, value in vars(QDS).items()
            if not name.startswith("_") and not callable(value)
        }
        self.assertEqual(public_methods, {"run", "run_forgery_attempt", "run_swap_test_example"})
        self.assertEqual(public_data, set())

    def test_noiseless_honest_run_accepts(self):
        qds = QDS(message_bits="101100", noise_channel="none", verbose=False)
        result = as_json(qds.run())
        self.assertEqual(result["verdict"], "ACCEPT_AUTHENTIC")
        self.assertEqual(result["failed_verifications"], 0)
        self.assertEqual(result["total_verifications"], 6 * 5)
        self.assertAlmostEqual(result["failure_rate"], 0.0)
        image_path = Path(result["generated_files"]["verification_decision"])
        self.assertTrue(image_path.exists())
        self.assertGreater(image_path.stat().st_size, 0)
        visualization = result["decision_visualization"]
        self.assertEqual(
            visualization["zones"]["green"]["range"],
            [0, result["authentic_threshold"]],
        )
        self.assertEqual(
            visualization["zones"]["yellow"]["range"],
            [result["authentic_threshold"], result["reject_threshold"]],
        )
        self.assertEqual(
            visualization["zones"]["red"]["range"],
            [result["reject_threshold"], result["total_verifications"]],
        )
        self.assertEqual(visualization["zones"]["green"]["colour"], "#e6f4ea")
        self.assertEqual(visualization["zones"]["yellow"]["colour"], "#fef7e0")
        self.assertEqual(visualization["zones"]["red"]["colour"], "#fce8e6")
        observed_point = visualization["points"][0]
        self.assertEqual(observed_point["location"][0], result["failed_verifications"])
        self.assertEqual(observed_point["colour"], "#2563eb")
        self.assertEqual(observed_point["verdict"], result["verdict"])

    def test_noiseless_counts_are_all_zero(self):
        qds = QDS(message_bits="10", L=8, M=2, n_qubits=2, shots=512, verbose=False)
        qds.run()
        for record in qds._last_result["raw_counts_summary"]:
            self.assertEqual(record["counts"], {"00": 512})

    def test_moderate_noise_still_accepts(self):
        # Small depolarizing noise should not flip the honest verdict.
        qds = QDS(
            message_bits="101100",
            noise_channel="depolarizing",
            noise_probability=0.05,
            verbose=False,
        )
        result = as_json(qds.run())
        self.assertEqual(result["verdict"], "ACCEPT_AUTHENTIC")


# --------------------------------------------------------------------------- #
# 2. Forgery / rejection path
# --------------------------------------------------------------------------- #
class TestForgeryPath(unittest.TestCase):
    def test_forgery_is_rejected(self):
        qds = QDS(message_bits="101100", noise_channel="none", verbose=False)
        result = as_json(qds.run_forgery_attempt())
        self.assertEqual(result["verdict"], "REJECT_FORGED")
        # A random-key forger fails essentially every check.
        self.assertEqual(result["failed_verifications"], result["total_verifications"])

    def test_forged_signature_keys_have_correct_length(self):
        qds = QDS(message_bits="11", L=10, M=3, verbose=False)
        forged = qds._forge_signature()
        for bit_index, entry in forged["revealed_keys"].items():
            self.assertEqual(len(entry["keys"]), qds._M)
            for key in entry["keys"]:
                self.assertEqual(len(key), qds._L)
                self.assertTrue(all(c in "01" for c in key))


# --------------------------------------------------------------------------- #
# 3. Verdict thresholds
# --------------------------------------------------------------------------- #
class TestVerdictThresholds(unittest.TestCase):
    def test_threshold_values(self):
        qds = QDS(message_bits="1010", M=5, c1=0.1, c2=0.4, verbose=False)
        result = as_json(qds.run())
        T = 4 * 5
        self.assertEqual(result["total_verifications"], T)
        self.assertAlmostEqual(result["authentic_threshold"], 0.1 * T)
        self.assertAlmostEqual(result["reject_threshold"], 0.4 * T)


# --------------------------------------------------------------------------- #
# 4. Reproducibility
# --------------------------------------------------------------------------- #
class TestReproducibility(unittest.TestCase):
    def test_same_seed_same_private_keys(self):
        a = QDS(message_bits="101", L=12, M=2, seed=7, verbose=False)
        b = QDS(message_bits="101", L=12, M=2, seed=7, verbose=False)
        a._generate_private_keys()
        b._generate_private_keys()
        self.assertEqual(a._private_keys, b._private_keys)

    def test_different_seed_different_private_keys(self):
        a = QDS(message_bits="101", L=12, M=2, seed=7, verbose=False)
        b = QDS(message_bits="101", L=12, M=2, seed=8, verbose=False)
        a._generate_private_keys()
        b._generate_private_keys()
        self.assertNotEqual(a._private_keys, b._private_keys)

    def test_rng_reset_makes_entry_point_independent(self):
        # Regression test: key generation must be reproducible regardless of
        # which public method triggers it (the RNG-consistency fix).
        qds = QDS(message_bits="10", L=8, M=2, seed=3, verbose=False)
        qds._generate_private_keys()
        keys_first = {k: list(v) for k, v in qds._private_keys.items()}
        # Trigger a separate generation path; keys must come out identical.
        qds.run_swap_test_example(make_plot=False)
        self.assertEqual(qds._private_keys, keys_first)


# --------------------------------------------------------------------------- #
# 5. Input validation
# --------------------------------------------------------------------------- #
class TestInputValidation(unittest.TestCase):
    def test_empty_message_rejected(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="", verbose=False)

    def test_non_binary_message_rejected(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10201", verbose=False)

    def test_non_string_message_rejected(self):
        with self.assertRaises(TypeError):
            QDS(message_bits=101, verbose=False)

    def test_thresholds_must_be_ordered(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10", c1=0.5, c2=0.4, verbose=False)

    def test_threshold_out_of_unit_interval(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10", c1=0.1, c2=1.5, verbose=False)

    def test_unknown_noise_channel_rejected(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10", noise_channel="gaussian", verbose=False)

    def test_noise_probability_out_of_range(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10", noise_probability=1.5, verbose=False)

    def test_n_qubits_cannot_exceed_L(self):
        with self.assertRaises(ValueError):
            QDS(message_bits="10", n_qubits=30, L=25, verbose=False)

    def test_bool_is_not_a_valid_integer_param(self):
        with self.assertRaises(TypeError):
            QDS(message_bits="10", n_qubits=True, verbose=False)


# --------------------------------------------------------------------------- #
# 6. Security margin warning
# --------------------------------------------------------------------------- #
class TestSecurityMargin(unittest.TestCase):
    def test_positive_margin_no_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # turn warnings into errors
            qds = QDS(message_bits="10", n_qubits=2, L=25, M=5, verbose=False)
            self.assertEqual(qds._security_margin, 25 - 2 * 5)
            self.assertEqual(qds._warnings, [])

    def test_non_positive_margin_is_reported_as_json_warning(self):
        qds = QDS(message_bits="10", n_qubits=4, L=20, M=5, verbose=False)
        self.assertEqual(len(qds._warnings), 1)
        result = as_json(qds.run())
        self.assertEqual(result["warnings"], qds._warnings)


# --------------------------------------------------------------------------- #
# 7. Key encoding internals
# --------------------------------------------------------------------------- #
class TestKeyEncoding(unittest.TestCase):
    def test_key_chunks_partition_full_key(self):
        qds = QDS(message_bits="1", n_qubits=4, L=25, verbose=False)
        key = "0" * 25
        chunks = qds._key_chunks(key)
        self.assertEqual(len(chunks), 4)
        self.assertEqual(sum(len(c) for c in chunks), 25)

    def test_zero_key_gives_zero_angles(self):
        qds = QDS(message_bits="1", n_qubits=4, L=8, verbose=False)
        angles = qds._rotation_angles_from_key("0" * 8)
        for angle in angles:
            self.assertAlmostEqual(angle, 0.0)

    def test_normalize_key_rejects_wrong_length(self):
        qds = QDS(message_bits="1", L=10, verbose=False)
        with self.assertRaises(ValueError):
            qds._normalize_key("0101")  # too short

    def test_normalize_key_accepts_iterable_of_bits(self):
        qds = QDS(message_bits="1", L=4, verbose=False)
        self.assertEqual(qds._normalize_key([0, 1, 1, 0]), "0110")


# --------------------------------------------------------------------------- #
# 8. SWAP-test diagnostic
# --------------------------------------------------------------------------- #
class TestSwapTest(unittest.TestCase):
    def test_ideal_vs_ideal_is_near_one(self):
        qds = QDS(message_bits="10", L=8, M=2, n_qubits=2, shots=2048, verbose=False)
        out = as_json(qds.run_swap_test_example(make_plot=False))
        p_same = out["comparisons"]["ideal_vs_ideal"]["p_ancilla_zero"]
        self.assertGreater(p_same, 0.95)

    def test_swap_test_keys_present(self):
        qds = QDS(message_bits="10", L=8, M=2, n_qubits=2, shots=1024, verbose=False)
        out = as_json(qds.run_swap_test_example(make_plot=False))
        self.assertIn("ideal_vs_received", out["comparisons"])
        self.assertIn("ideal_vs_complementary", out["comparisons"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
