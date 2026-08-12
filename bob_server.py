"""
Bob Server for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Bob receiver server. It exposes FastAPI endpoints
representing quantum and classical communication channels. It:
  - Receives qubits (QASM), measures them with randomly chosen bases.
  - Participates in basis sifting and QBER estimation.
  - Runs the Cascade error reconciliation protocol (calling back to Alice's
    parity-check and key-confirmation APIs).
  - Receives Alice's encrypted message, applies Toeplitz privacy amplification,
    and decrypts using the final secret key.

Supports realistic channel noise: depolarization errors during measurement.
"""

import os
import random
import hashlib
import base64
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
import qiskit.qasm2 as qasm2
from cryptography.fernet import Fernet
from fastapi.middleware.cors import CORSMiddleware
from cascade import (
    Cascade,
    toeplitz_hash,
    serfling_upper_bound,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL of Alice's client server — used for Cascade callback APIs
ALICE_URL = os.getenv("ALICE_CLIENT_URL", "http://localhost:8001")

# Bob's internal state (dict-based to handle photon loss / index mismatch)
bob_bases: dict = {}           # {photon_index: basis}
bob_measured_bits: dict = {}   # {photon_index: measured_bit}
bob_reconciled_key: list = []  # Corrected key list after Cascade (set in check_qber)


class QubitPayload(BaseModel):
    qasm_strings: list[str]
    received_indices: list[int]
    depolarization_rate: float = 0.02


class QberPayload(BaseModel):
    sample_indices: list[int]
    sample_bits: list[int]
    matching_indices: list[int]
    epsilon: float


class ChatReceivePayload(BaseModel):
    encrypted_message: str
    toeplitz_seed: int
    final_len: int


@app.post("/quantum_channel/receive")
def receive_qubits(payload: QubitPayload):
    """
    Quantum Channel Endpoint.

    Receives QASM strings representing qubits from Alice (only those that
    survived fiber attenuation), reconstructs QuantumCircuit objects, and
    simulates measurement using Bob's randomly generated bases. Results are
    stored in Bob's internal state as {photon_index: bit_value}.
    """
    global bob_bases, bob_measured_bits
    bob_measured_bits = {}
    bob_bases = {}

    # Build Qiskit Aer NoiseModel for depolarization during measurement
    noise_model = NoiseModel()
    if payload.depolarization_rate > 0:
        error = depolarizing_error(payload.depolarization_rate, 1)
        noise_model.add_all_qubit_quantum_error(error, ["h", "x", "measure"])

    simulator = AerSimulator(noise_model=noise_model)

    for idx, qasm_str in zip(payload.received_indices, payload.qasm_strings):
        qc = qasm2.loads(qasm_str)

        # Bob randomly selects a measurement basis for this photon
        basis = random.randint(0, 1)
        bob_bases[idx] = basis

        # Apply Hadamard if measuring in X basis, then measure
        if basis == 1:
            qc.h(0)
        qc.measure(0, 0)

        result = simulator.run(qc, shots=1).result().get_counts()
        bit = int(list(result.keys())[0])
        bob_measured_bits[idx] = bit

    return {"status": "success", "measured_count": len(bob_measured_bits)}


@app.get("/classical_channel/bases")
def get_bob_bases():
    """Return Bob's measurement bases as a dict keyed by photon index."""
    return {"bob_bases": bob_bases}


@app.post("/classical_channel/check_qber")
def check_qber(payload: QberPayload):
    """
    Classical Channel Endpoint — QBER Verification + Cascade Reconciliation.

    Receives a test sample from Alice, computes the QBER and its Serfling
    upper bound. If the bound is within the 11% security threshold, Bob:
      1. Constructs his raw sifted key from the matching indices minus sample.
      2. Runs the Cascade error reconciliation protocol, calling back to
         Alice's /parity_check and /confirm_key APIs for each block comparison.
      3. Stores the reconciled key for later use in /chat/receive.

    Returns QBER stats, raw/reconciled keys, Cascade statistics, and whether
    the reconciliation achieved a confirmed key match with Alice.
    """
    global bob_reconciled_key

    mismatches = 0
    total_sample = len(payload.sample_indices)

    if total_sample == 0:
        return {"qber": 1.0, "qber_bound": 1.0, "mismatches": 0, "bob_measured_bits": bob_measured_bits}

    for i in range(total_sample):
        idx = payload.sample_indices[i]
        if payload.sample_bits[i] != bob_measured_bits.get(idx):
            mismatches += 1

    qber = mismatches / total_sample
    qber_bound = serfling_upper_bound(
        qber,
        len(payload.matching_indices),
        len(payload.sample_indices),
        payload.epsilon,
    )

    if qber_bound > 0.11:
        # Channel is insecure — do not run Cascade
        return {
            "qber": qber,
            "qber_bound": qber_bound,
            "bob_measured_bits": bob_measured_bits,
            "mismatches": mismatches,
        }

    # --- Build Bob's raw sifted key (same ordering as Alice's alice_raw_key) ---
    sample_set = set(payload.sample_indices)
    bob_raw_key_original = [
        bob_measured_bits[idx]
        for idx in payload.matching_indices
        if idx not in sample_set
    ]

    # Work on a copy so we can return both the original and the corrected version
    bob_reconciled = bob_raw_key_original[:]

    # --- Define Cascade callbacks (HTTP calls to Alice) ---
    def alice_parity_fn(block: list) -> int:
        """Call Alice's parity check API and return her parity for this block."""
        res = requests.post(
            f"{ALICE_URL}/classical_channel/parity_check",
            json={"block_indices": block},
            timeout=30,
        )
        return res.json()["parity"]

    def confirm_key_fn(bob_key: list) -> bool:
        """
        Compute SHA-256 hash of Bob's current key string and ask Alice if
        it matches her key. Used for early termination in Cascade.
        """
        bob_hash = hashlib.sha256(
            "".join(str(b) for b in bob_key).encode()
        ).hexdigest()
        res = requests.post(
            f"{ALICE_URL}/classical_channel/confirm_key",
            json={"bob_key_hash": bob_hash},
            timeout=30,
        )
        return res.json()["match"]

    # --- Run Cascade ---
    cascade = Cascade(
        bob_reconciled,
        qber_bound,
        alice_parity_fn,
        confirm_key_fn,
        num_passes=4,
        verbose=True,
    )
    corrections = cascade.run()
    leaked_bits = cascade.leaked_bits

    # Final key-match confirmation
    is_final_key_matched = confirm_key_fn(bob_reconciled)

    # Persist reconciled key for /chat/receive
    bob_reconciled_key = bob_reconciled

    return {
        "qber": qber,
        "qber_bound": qber_bound,
        "bob_measured_bits": bob_measured_bits,
        "mismatches": mismatches,
        "bob_raw_key": bob_raw_key_original,
        "bob_reconciled_key": bob_reconciled,
        "leaked_bits": leaked_bits,
        "corrections": corrections,
        "is_final_key_matched": is_final_key_matched,
    }


@app.post("/chat/receive")
def receive_secret_message(payload: ChatReceivePayload):
    """
    Classical Channel Endpoint — Decryption.

    Receives Alice's encrypted message along with the shared Toeplitz seed and
    the agreed final key length. Bob applies Toeplitz privacy amplification to
    his reconciled key using the same parameters as Alice, then decrypts the
    message using the derived secret key.

    Always returns bob_secret_final_key (the Toeplitz-hashed key) regardless
    of whether decryption succeeds, so the frontend can compare both sides.
    """
    if not bob_reconciled_key:
        return {
            "status": "error",
            "message": "Bob does not have a reconciled key yet.",
            "bob_secret_final_key": "",
            "bob_reconciled_key": [],
        }

    if payload.final_len <= 0:
        return {
            "status": "error",
            "message": "final_len must be a positive integer.",
            "bob_secret_final_key": "",
            "bob_reconciled_key": bob_reconciled_key,
        }

    # Apply Toeplitz privacy amplification to derive the secret key
    reconciled_key_str = "".join(str(b) for b in bob_reconciled_key)
    bob_secret_final_key = toeplitz_hash(reconciled_key_str, payload.final_len, payload.toeplitz_seed)

    # Convert binary secret key to an AES key (Fernet via SHA-256)
    key_hash = hashlib.sha256(bob_secret_final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)

    try:
        decrypted_bytes = cipher.decrypt(payload.encrypted_message.encode())
        plain_text = decrypted_bytes.decode()
        print(f"[Bob] Message decrypted successfully: {plain_text}")
        return {
            "status": "success",
            "decrypted_message": plain_text,
            "bob_secret_final_key": bob_secret_final_key,
            "bob_reconciled_key": bob_reconciled_key,
        }

    except Exception:
        print(f"[Bob] Decryption failed. bob_secret_final_key[:20]={bob_secret_final_key[:20]}")
        return {
            "status": "error",
            "message": "Decryption failed — key mismatch after privacy amplification.",
            "bob_secret_final_key": bob_secret_final_key,
            "bob_reconciled_key": bob_reconciled_key,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
