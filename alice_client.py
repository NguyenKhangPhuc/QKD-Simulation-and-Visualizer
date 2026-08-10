"""
Alice Client for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Alice client. It generates random raw bits and quantum
bases, encodes the bits into qubits (represented as QASM strings), simulates
eavesdropping by Eve (if enabled), transmits the qubits to Bob's server,
performs basis sifting and QBER (Quantum Bit Error Rate) checks classically,
derives the final secret key, and uses it to encrypt a confidential message
sent to Bob.

Supports realistic channel noise: fiber attenuation, depolarization, dark counts,
and variable Eve interception probability.
"""

import random
import requests
import os
import hashlib
import base64
from qiskit import QuantumCircuit
import qiskit.qasm2 as qasm2
from cryptography.fernet import Fernet
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

from channel_model import RealisticQuantumChannel

SERVER_URL = os.getenv("BOB_SERVER_URL", "http://localhost:8000")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FrontEndInitializePayload(BaseModel):
    num_bits: int
    is_eve: bool = False
    distance_km: float = 10.0
    depolarization_rate: float = 0.02
    eve_intercept_prob: float = 1.0


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


def encode_bit(bit, base):
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


@app.post("/initialize_connection")
def initialize_connection(payload: FrontEndInitializePayload):
    """
    Initialize the BB84 QKD protocol simulation with realistic channel noise.

    This endpoint orchestrates the entire QKD flow:
    1. Generates random bits and bases for Alice.
    2. Encodes bits into qubits (QASM strings).
    3. Passes qubits through a realistic channel model (Eve interception,
       fiber attenuation, depolarization noise, dark counts).
    4. Transmits surviving photons to Bob via HTTP.
    5. Performs basis sifting over the classical channel (only for detected photons).
    6. Checks QBER (Quantum Bit Error Rate) on a 20% sample.
    7. If QBER <= 11%, derives the final secret key and encrypts a test message.
    """
    # 1. Generate Raw Bits & Bases
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
    )
    received_qasm, received_indices, eve_info, noise_model = channel.transmit(
        qasm_strings
    )

    print(f"Sent {payload.num_bits} photons. Received and detected by Bob: {len(received_qasm)}")

    # 4. Transmit surviving photons to Bob
    print("Sending Qubits over Quantum Channel (HTTP POST)...")
    res = requests.post(
        f"{SERVER_URL}/quantum_channel/receive",
        json={
            "qasm_strings": received_qasm,
            "received_indices": received_indices,
            "depolarization_rate": payload.depolarization_rate,
        },
    )
    print("Bob's response:", res.json())

    # 5. Sifting (Fetch Bob's bases for detected photons)
    print("\n--- [2] SIFTING (Getting Bob's bases) ---")
    res = requests.get(f"{SERVER_URL}/classical_channel/bases")
    bob_bases = res.json()["bob_bases"]

    # Filter matching bases ONLY for photons that actually arrived
    matching_indices = [i for i in received_indices if alice_bases[i] == bob_bases[i]]
    print(f"Number of bits with matching bases: {len(matching_indices)}")

    # 6. QBER Calculation
    print("\n--- [3] QBER VERIFICATION ---")
    sample_size = int(len(matching_indices) * 0.2)
    sample_indices = random.sample(matching_indices, sample_size) if sample_size > 0 else []
    sample_bits = [alice_bits[i] for i in sample_indices]

    print("Sending QBER test sample to Bob (HTTP POST)...")
    res = requests.post(
        f"{SERVER_URL}/classical_channel/check_qber",
        json={
            "sample_indices": sample_indices,
            "sample_bits": sample_bits,
            "matching_indices": matching_indices,
        },
    )
    qber = res.json()["qber"]
    bob_measured_bits_dict = res.json()["bob_measured_bits"]
    mismatches = res.json().get("mismatches", 0)
    print(f"QBER calculated by Bob: {qber * 100}%")

    if qber > 0.11:
        print("❌ Eavesdropper detected, aborting key!")
        return {
            "status": "aborted",
            "reason": "QBER threshold exceeded (>11%)",
            "qber": qber,
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

    # 7. Derive Final Secret Key
    print("✅ Channel is secure! Generating Final Key.")
    final_key = "".join([str(alice_bits[i]) for i in matching_indices if i not in sample_indices])
    print(f"Alice's Key: {final_key[:40]}...")

    # 8. Encrypt & Send Secret Message
    print("\n--- [4] KEY APPLICATION (ENCRYPTING MESSAGE) ---")
    secret_message = "The secret base coordinates are: 10.762, 106.681. Do not share with anyone!"
    print(f"Original message: '{secret_message}'")

    # Convert the binary final_key to an AES key (Fernet)
    key_hash = hashlib.sha256(final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)

    # Encrypt the message
    encrypted_bytes = cipher.encrypt(secret_message.encode())
    encrypted_message = encrypted_bytes.decode()
    print(f"Message encrypted to: {encrypted_message[:50]}...")

    # Send the encrypted message over the public network
    print("Sending over the Internet to Bob...")
    res = requests.post(
        f"{SERVER_URL}/chat/receive",
        json={"encrypted_message": encrypted_message},
    )
    bob_final_key = res.json().get("bob_final_key", "")

    return {
        "status": "success",
        "qber": qber,
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
        "alice_final_key": final_key,
        "bob_final_key": bob_final_key,
        "encrypted_message": encrypted_message,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
