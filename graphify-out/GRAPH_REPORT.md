# Graph Report - .  (2026-06-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 80 nodes · 146 edges · 12 communities (4 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2bfe135f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]

## God Nodes (most connected - your core abstractions)
1. `QuantumDigitalSignatureWithChannelNoise` - 40 edges
2. `TestInputValidation` - 11 edges
3. `QuantumCircuit` - 7 edges
4. `TestHonestWorkflow` - 6 edges
5. `TestKeyEncoding` - 6 edges
6. `TestReproducibility` - 5 edges
7. `_main()` - 4 edges
8. `TestForgeryPath` - 4 edges
9. `TestSecurityMargin` - 4 edges
10. `TestSwapTest` - 4 edges

## Surprising Connections (you probably didn't know these)
- `TestForgeryPath` --uses--> `QuantumDigitalSignatureWithChannelNoise`  [INFERRED]
  test_quantum_digital_signature.py → quantum_digital_signature_channel_noise.py
- `TestHonestWorkflow` --uses--> `QuantumDigitalSignatureWithChannelNoise`  [INFERRED]
  test_quantum_digital_signature.py → quantum_digital_signature_channel_noise.py
- `TestInputValidation` --uses--> `QuantumDigitalSignatureWithChannelNoise`  [INFERRED]
  test_quantum_digital_signature.py → quantum_digital_signature_channel_noise.py
- `TestKeyEncoding` --uses--> `QuantumDigitalSignatureWithChannelNoise`  [INFERRED]
  test_quantum_digital_signature.py → quantum_digital_signature_channel_noise.py
- `TestReproducibility` --uses--> `QuantumDigitalSignatureWithChannelNoise`  [INFERRED]
  test_quantum_digital_signature.py → quantum_digital_signature_channel_noise.py

## Import Cycles
- None detected.

## Communities (12 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.22
Nodes (5): Any, Honest signature: reveal the correct private keys for each message bit., Adversarial signature: a forger who does not know the private keys         guess, Run the full honest QDS workflow end-to-end and return the verdict., Run the protocol but verify against a forged (random-key) signature.          De

### Community 1 - "Community 1"
Cohesion: 0.22
Nodes (3): QuantumDigitalSignatureWithChannelNoise, Copy an ideal public-key circuit and append channel noise to each qubit., Class-based Gottesman-Chuang style QDS protocol.      The class stores ideal pub

### Community 3 - "Community 3"
Cohesion: 0.39
Nodes (3): Build only the ideal noiseless state-preparation circuit for |f_k>., Build the ideal inverse circuit from a revealed classical private key., QuantumCircuit

### Community 6 - "Community 6"
Cohesion: 0.50
Nodes (3): _main(), Class-based Gottesman-Chuang style Quantum Digital Signature (QDS) protocol with, Single entry point: run the full QDS protocol once and print the verdict.

## Knowledge Gaps
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QuantumDigitalSignatureWithChannelNoise` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.762) - this node is a cross-community bridge._
- **Why does `TestInputValidation` connect `Community 2` to `Community 1`, `Community 7`?**
  _High betweenness centrality (0.216) - this node is a cross-community bridge._
- **Why does `TestHonestWorkflow` connect `Community 4` to `Community 1`, `Community 7`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `QuantumDigitalSignatureWithChannelNoise` (e.g. with `TestForgeryPath` and `TestHonestWorkflow`) actually correct?**
  _`QuantumDigitalSignatureWithChannelNoise` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Class-based Gottesman-Chuang style Quantum Digital Signature (QDS) protocol with`, `Class-based Gottesman-Chuang style QDS protocol.      The class stores ideal pub`, `Build only the ideal noiseless state-preparation circuit for |f_k>.` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._