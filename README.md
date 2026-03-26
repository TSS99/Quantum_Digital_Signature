# Quantum Digital Signature (QDS)

A Python implementation of the **Gottesman-Chuang Quantum Digital Signature** scheme — a way to sign messages using the laws of quantum physics instead of traditional math-based cryptography.

> Based on: D. Gottesman & I. L. Chuang, *"Quantum Digital Signatures"*, arXiv:quant-ph/0105032 (2001)

---

## What Is This?

A **digital signature** is a way for someone (Alice) to prove she sent a message — and that the message wasn't tampered with. Normally this relies on hard math problems (like factoring large numbers).

This project implements a **quantum** version: security comes from the laws of quantum physics itself — specifically, the fact that you can't perfectly copy an unknown quantum state (the **no-cloning theorem**) and that quantum measurements disturb the system you're measuring (**Holevo's theorem**).

Even a quantum computer can't break this scheme.

---
