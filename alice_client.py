"""
Alice Client for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Alice client. It:
  - Generates random raw bits and quantum bases.
  - Encodes bits into qubits (QASM strings) and transmits them to Bob.
  - Simulates eavesdropping by Eve (optional).
  - Performs basis sifting and QBER estimation.
  - Exposes parity-check and key-confirmation callback APIs consumed by Bob's
    Cascade reconciliation protocol.
  - Applies Toeplitz privacy amplification and encrypts a secret message.

Supports realistic channel noise: fiber attenuation, depolarization, dark
counts, and variable Eve interception probability.
"""

import random
import hashlib
import requests
import os
import base64
from qiskit import QuantumCircuit
import qiskit.qasm2 as qasm2
from cryptography.fernet import Fernet
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from channel_model import RealisticQuantumChannel
from cascade import get_parity, toeplitz_hash, generate_toeplitz_matrix

SERVER_URL = os.getenv("BOB_SERVER_URL", "http://localhost:8000")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Module-level state: stores Alice's raw key for the current simulation session.
# Cascade (running on Bob's side) calls back to the parity_check and
# confirm_key endpoints below, which read this variable.
# --------------------------------------------------------------------------
alice_raw_key: list = []


# --------------------------------------------------------------------------
# Request / Response models
# --------------------------------------------------------------------------

class FrontEndInitializePayload(BaseModel):
    num_bits: int
    is_eve: bool = False
    distance_km: float = 10.0
    depolarization_rate: float = 0.02
    eve_intercept_prob: float = 1.0
    detector_efficiency: float = 0.85
    epsilon: float = 1e-6


class ParityCheckPayload(BaseModel):
    block_indices: list[int]


class ConfirmKeyPayload(BaseModel):
    bob_key_hash: str


# --------------------------------------------------------------------------
# Cascade callback endpoints (called by Bob's server during reconciliation)
# --------------------------------------------------------------------------

@app.post("/classical_channel/parity_check")
def parity_check(payload: ParityCheckPayload):
    """
    Cascade Callback Endpoint — Parity Check.

    Called by Bob's Cascade implementation for each block comparison and each
    step of the binary search. Returns Alice's XOR parity for the given block
    indices into alice_raw_key. Each successful call leaks exactly 1 bit of
    information to the public channel.

    Args (in body):
        block_indices: List of integer indices into alice_raw_key.

    Returns:
        {"parity": 0 | 1}
    """
    parity = get_parity(alice_raw_key, payload.block_indices)
    return {"parity": parity}


@app.post("/classical_channel/confirm_key")
def confirm_key(payload: ConfirmKeyPayload):
    """
    Cascade Callback Endpoint — Key Confirmation.

    Called by Bob's Cascade at the end of each pass (for early termination)
    and after the final cleanup round. Alice computes the SHA-256 hash of her
    raw key string and compares it with Bob's hash. This reveals only the hash
    (not the key content) and allows Bob to verify convergence without
    transmitting the key itself.

    Args (in body):
        bob_key_hash: Hex-encoded SHA-256 hash of Bob's current reconciled key.

    Returns:
        {"match": true | false}
    """
    alice_hash = hashlib.sha256(
        "".join(str(b) for b in alice_raw_key).encode()
    ).hexdigest()
    return {"match": alice_hash == payload.bob_key_hash}


# --------------------------------------------------------------------------
# Core QKD helper functions
# --------------------------------------------------------------------------

def generate_bits_and_base(num_bits: int):
    """
    Generate random binary bits and bases for QKD.

    Args:
        num_bits (int): The number of bits to generate.

    Returns:
        tuple: A tuple containing two lists:
            - bits (list of int): Randomly generated bits (0 or 1).
            - bases (list of int): Randomly generated bases (0 for Z, 1 for X).
    """
    bits = [random.randint(0, 1) for _ in range(num_bits)]
    bases = [random.randint(0, 1) for _ in range(num_bits)]
    return bits, bases


def encode_bit(bit: int, base: int) -> QuantumCircuit:
    """
    Encode a binary bit into a quantum state (qubit) based on a given basis.

    Args:
        bit (int): The binary value to encode (0 or 1).
        base (int): The basis to encode in (0 for Z basis, 1 for X basis).

    Returns:
        QuantumCircuit: A quantum circuit representing the encoded state.
    """
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if base == 1:
        qc.h(0)
    return qc


# --------------------------------------------------------------------------
# Main QKD simulation endpoint
# --------------------------------------------------------------------------

@app.post("/initialize_connection")
def initialize_connection(payload: FrontEndInitializePayload):
    """
    Initialize the BB84 QKD protocol simulation with realistic channel noise.

    Orchestrates the full QKD flow:
      1.  Generate Alice's random bits and bases.
      2.  Encode bits into qubits (QASM strings).
      3.  Pass qubits through realistic channel model (Eve, attenuation, noise).
      4.  Transmit surviving photons to Bob via /quantum_channel/receive.
      5.  Sifting: fetch Bob's bases and compute matching indices.
      6.  QBER estimation on a 20% sample; compute Serfling upper bound.
      7.  Store alice_raw_key at module level for Cascade callback endpoints.
      8.  Call Bob's /classical_channel/check_qber — Bob runs Cascade internally,
          calling /parity_check and /confirm_key on this server concurrently.
      9.  If QBER bound exceeds 11%, abort.
      10. Compute final_len for Toeplitz privacy amplification.
      11. Apply Toeplitz hash to alice_raw_key using a shared random seed.
      12. Encrypt a test message and send it to Bob's /chat/receive.
      13. Return full simulation result to the frontend.
    """
    global alice_raw_key

    # 1. Generate raw bits and bases
    alice_bits, alice_bases = generate_bits_and_base(payload.num_bits)

    # 2. Encode bits into QASM strings
    qasm_strings = []
    for i in range(payload.num_bits):
        qc = encode_bit(alice_bits[i], alice_bases[i])
        qasm_strings.append(qasm2.dumps(qc))

    # 3. Pass through realistic channel model
    channel = RealisticQuantumChannel(
        distance_km=payload.distance_km,
        depolarization_rate=payload.depolarization_rate,
        is_eve=payload.is_eve,
        eve_intercept_prob=payload.eve_intercept_prob,
        detector_efficiency=payload.detector_efficiency,
    )
    received_qasm, received_indices, eve_info, _ = channel.transmit(qasm_strings)

    print(f"Sent {payload.num_bits} photons. Received by Bob: {len(received_qasm)}")

    # 4. Transmit surviving photons to Bob
    print("Sending qubits over the quantum channel...")
    res = requests.post(
        f"{SERVER_URL}/quantum_channel/receive",
        json={
            "qasm_strings": received_qasm,
            "received_indices": received_indices,
            "depolarization_rate": payload.depolarization_rate,
        },
    )
    print("Bob's measurement response:", res.json())

    # 5. Sifting — fetch Bob's bases and find matching indices
    print("\n--- [2] SIFTING ---")
    res = requests.get(f"{SERVER_URL}/classical_channel/bases")
    bob_bases = res.json()["bob_bases"]

    # bob_bases keys are strings after JSON serialization
    matching_indices = [
        i for i in received_indices
        if str(i) in bob_bases and alice_bases[i] == bob_bases[str(i)]
    ]
    print(f"Matching basis indices: {len(matching_indices)}")

    # 6. QBER sample
    print("\n--- [3] QBER VERIFICATION ---")
    sample_size = int(len(matching_indices) * 0.2)
    sample_indices = random.sample(matching_indices, sample_size) if sample_size > 0 else []
    sample_bits = [alice_bits[i] for i in sample_indices]

    # 7. Compute alice_raw_key and store at module level BEFORE calling check_qber,
    #    so that Bob can call back to /parity_check while check_qber is in-flight.
    sample_set = set(sample_indices)
    alice_raw_key = [alice_bits[i] for i in matching_indices if i not in sample_set]

    print("Sending QBER sample to Bob (Bob will run Cascade internally)...")
    res = requests.post(
        f"{SERVER_URL}/classical_channel/check_qber",
        json={
            "sample_indices": sample_indices,
            "sample_bits": sample_bits,
            "matching_indices": matching_indices,
            "epsilon": payload.epsilon,
        },
        timeout=300,  # Cascade can take time; generous timeout
    )

    qber = res.json()["qber"]
    qber_bound = res.json()["qber_bound"]
    bob_measured_bits_dict = res.json()["bob_measured_bits"]
    mismatches = res.json().get("mismatches", 0)
    print(f"QBER: {qber * 100:.2f}%  |  Serfling bound: {qber_bound * 100:.2f}%")

    # 9. Abort if channel is insecure
    if qber_bound > 0.11:
        print("Eavesdropper detected — aborting key exchange.")
        return {
            "status": "aborted",
            "reason": "QBER threshold exceeded (>11%)",
            "qber": qber,
            "qber_bound": qber_bound,
            "mismatches": mismatches,
            "received_photon_count": len(received_indices),
            "initial_alice_bits": alice_bits,
            "initial_alice_bases": alice_bases,
            "eve_bases": eve_info.get("eve_bases", []),
            "eve_measured_bits": eve_info.get("eve_measured_bits", []),
            "initial_bob_bases": bob_bases,
            "initial_bob_bits": bob_measured_bits_dict,
            "matching_indices_alice_bob": matching_indices,
            "sample_size_qber": sample_size,
            "sample_indices_qber": sample_indices,
            "sample_bits_qber": sample_bits,
        }

    # Read Cascade results from Bob's check_qber response
    bob_raw_key_list = res.json().get("bob_raw_key", [])
    bob_reconciled_key_list = res.json().get("bob_reconciled_key", [])
    leaked_bits = res.json().get("leaked_bits", 0)
    corrections = res.json().get("corrections", 0)
    is_final_key_matched = res.json().get("is_final_key_matched", False)

    print(f"Cascade: {corrections} corrections, {leaked_bits} bits leaked, match={is_final_key_matched}")

    # 10. Compute final_len for privacy amplification
    security_margin = 20
    leaked_total = sample_size + leaked_bits
    final_len = max(1, len(alice_raw_key) - leaked_total - security_margin)

    # 11. Apply Toeplitz hash to alice_raw_key
    toeplitz_seed = random.randint(0, 2**32 - 1)
    alice_raw_key_str = "".join(str(b) for b in alice_raw_key)
    alice_secret_final_key = toeplitz_hash(alice_raw_key_str, final_len, toeplitz_seed)
    toeplitz_matrix_data = generate_toeplitz_matrix(len(alice_raw_key), final_len, toeplitz_seed).tolist()
    print(f"Privacy amplification: {len(alice_raw_key_str)} -> {final_len} bits (seed={toeplitz_seed})")

    # 12. Encrypt test message and send to Bob
    print("\n--- [4] ENCRYPTING & SENDING MESSAGE ---")
    secret_message = "The secret base coordinates are: 10.762, 106.681. Do not share with anyone!"
    print(f"Original message: '{secret_message}'")

    key_hash = hashlib.sha256(alice_secret_final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)
    encrypted_bytes = cipher.encrypt(secret_message.encode())
    encrypted_message = encrypted_bytes.decode()

    print(f"Encrypted: {encrypted_message[:60]}...")
    print("Sending to Bob...")
    res = requests.post(
        f"{SERVER_URL}/chat/receive",
        json={
            "encrypted_message": encrypted_message,
            "toeplitz_seed": toeplitz_seed,
            "final_len": final_len,
        },
    )
    bob_secret_final_key = res.json().get("bob_secret_final_key", "")
    print(f"Bob response status: {res.json().get('status')}")

    return {
        "status": "success",
        "qber": qber,
        "qber_bound": qber_bound,
        "mismatches": mismatches,
        "received_photon_count": len(received_indices),
        "initial_alice_bits": alice_bits,
        "initial_alice_bases": alice_bases,
        "eve_bases": eve_info.get("eve_bases", []),
        "eve_measured_bits": eve_info.get("eve_measured_bits", []),
        "initial_bob_bases": bob_bases,
        "initial_bob_bits": bob_measured_bits_dict,
        "matching_indices_alice_bob": matching_indices,
        "sample_size_qber": sample_size,
        "sample_indices_qber": sample_indices,
        "sample_bits_qber": sample_bits,
        # Key progression
        "alice_raw_key": alice_raw_key_str,
        "alice_reconciled_key": alice_raw_key_str,  # Alice's key has no errors to fix
        "alice_secret_final_key": alice_secret_final_key,
        "bob_raw_key": "".join(str(b) for b in bob_raw_key_list),
        "bob_reconciled_key": "".join(str(b) for b in bob_reconciled_key_list),
        "bob_secret_final_key": bob_secret_final_key,
        # Cascade statistics
        "leaked_bits": leaked_bits,
        "corrections": corrections,
        "is_final_key_matched": is_final_key_matched,
        # Toeplitz Matrix
        "toeplitz_matrix": toeplitz_matrix_data,
        # Encryption
        "encrypted_message": encrypted_message,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
