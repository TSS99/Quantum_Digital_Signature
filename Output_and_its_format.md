# Output and Its Format

This document describes the compact JSON strings returned by the public methods
`run()`, `run_forgery_attempt()`, and `run_swap_test_example()`, plus the JSON
events printed when `verbose=True`.

---

## 1. Verification Result JSON

`run()` and `run_forgery_attempt()` both return a JSON string. Decoded, it has
this compact shape:

```json
{
  "message_bits": "101100",
  "verdict": "ACCEPT_AUTHENTIC",
  "failed_verifications": 0,
  "total_verifications": 30,
  "failure_rate": 0.0,
  "authentic_threshold": 3.0,
  "reject_threshold": 12.0,
  "security_margin": 5,
  "noise_channel": "depolarizing",
  "noise_probability": 0.05,
  "warnings": [],
  "generated_files": {
    "verification_decision": "verification_decision.png"
  },
  "decision_visualization": {
    "zones": {
      "green": {
        "label": "ACCEPT_AUTHENTIC",
        "range": [0, 3.0],
        "colour": "#e6f4ea"
      },
      "yellow": {
        "label": "INCONCLUSIVE",
        "range": [3.0, 12.0],
        "colour": "#fef7e0"
      },
      "red": {
        "label": "REJECT_FORGED",
        "range": [12.0, 30],
        "colour": "#fce8e6"
      }
    },
    "thresholds": [
      {
        "label": "c1*T",
        "location": 3.0,
        "colour": "#10b981"
      },
      {
        "label": "c2*T",
        "location": 12.0,
        "colour": "#f43f5e"
      }
    ],
    "points": [
      {
        "label": "observed_failures",
        "location": [0, 0.15],
        "colour": "#2563eb",
        "verdict": "ACCEPT_AUTHENTIC"
      }
    ],
    "axes": {
      "x": {
        "label": "Failed verification checks",
        "range": [0, 30]
      },
      "y": {
        "label": "Decision marker height",
        "range": [0, 1]
      }
    }
  }
}
```

The long raw simulator sections (`per_bit_results`, `copy_results`, and
`raw_counts_summary`) are intentionally not included in public JSON output.
`verification_decision.png` is generated as an image artifact showing the
accept, inconclusive, and reject decision zones.
`decision_visualization` is the JSON version of the same visual information:
zone ranges, zone colours, threshold locations, axes, and the observed failure
point location.

### `verdict`

| Verdict | Condition | Meaning |
|---------|-----------|---------|
| `"ACCEPT_AUTHENTIC"` | `s <= c1 * T` | Few enough failures; signature accepted. |
| `"REJECT_FORGED"` | `s >= c2 * T` | Too many failures; signature rejected. |
| `"INCONCLUSIVE"` | `c1*T < s < c2*T` | In between; verdict withheld. |

where `s = failed_verifications` and `T = total_verifications`.

---

## 2. Printed JSON Events

When `verbose=True`, the constructor prints a compact configuration event and
`run()` / `run_forgery_attempt()` prints a compact result event.

```json
{
  "event": "result",
  "result": {
    "message_bits": "101100",
    "verdict": "ACCEPT_AUTHENTIC",
    "failed_verifications": 0,
    "total_verifications": 30,
    "failure_rate": 0.0,
    "authentic_threshold": 3.0,
    "reject_threshold": 12.0,
    "security_margin": 5,
    "noise_channel": "depolarizing",
    "noise_probability": 0.05,
    "warnings": [],
    "generated_files": {
      "verification_decision": "verification_decision.png"
    },
    "decision_visualization": {
      "zones": {
        "green": {
          "label": "ACCEPT_AUTHENTIC",
          "range": [0, 3.0],
          "colour": "#e6f4ea"
        },
        "yellow": {
          "label": "INCONCLUSIVE",
          "range": [3.0, 12.0],
          "colour": "#fef7e0"
        },
        "red": {
          "label": "REJECT_FORGED",
          "range": [12.0, 30],
          "colour": "#fce8e6"
        }
      },
      "thresholds": [
        {
          "label": "c1*T",
          "location": 3.0,
          "colour": "#10b981"
        },
        {
          "label": "c2*T",
          "location": 12.0,
          "colour": "#f43f5e"
        }
      ],
      "points": [
        {
          "label": "observed_failures",
          "location": [0, 0.15],
          "colour": "#2563eb",
          "verdict": "ACCEPT_AUTHENTIC"
        }
      ],
      "axes": {
        "x": {
          "label": "Failed verification checks",
          "range": [0, 30]
        },
        "y": {
          "label": "Decision marker height",
          "range": [0, 1]
        }
      }
    }
  }
}
```

The command-line entry point prints one compact JSON result document.

---

## 3. SWAP-Test JSON

`run_swap_test_example(...)` returns a JSON string. Decoded, it has this compact
shape:

```json
{
  "bit_index": 0,
  "copy_index": 0,
  "bit_value": 1,
  "comparisons": {
    "ideal_vs_ideal": {
      "p_ancilla_zero": 1.0
    },
    "ideal_vs_received": {
      "p_ancilla_zero": 0.95
    },
    "ideal_vs_complementary": {
      "p_ancilla_zero": 0.5
    }
  }
}
```

If `make_plot=True`, a compact JSON `plot` object is included with bar-chart
series values. No Matplotlib chart is displayed.

---

## 4. Errors

Invalid input raises:

- `TypeError` for wrong types, such as non-integer `n_qubits`.
- `ValueError` for out-of-range values, such as `c1 >= c2`.
- `RuntimeError` if verification is attempted before keys/public keys exist.

When running the module as a script, uncaught errors are printed as JSON error
objects before the process exits with code `1`.
