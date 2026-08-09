"""
Alice Client for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Alice client. It generates random raw bits and quantum 
bases, encodes the bits into qubits (represented as QASM strings), simulates 
eavesdropping by Eve (if enabled), transmits the qubits to Bob's server, 
performs basis sifting and QBER (Quantum Bit Error Rate) checks classically, 
derives the final secret key, and uses it to encrypt a confidential message 
sent to Bob.
"""

import random
import requests
import os
from qiskit import QuantumCircuit
import qiskit.qasm2 as qasm2
import hashlib
import base64
from cryptography.fernet import Fernet
from fastapi import FastAPI, Body
from pydantic import BaseModel
from qiskit_aer import AerSimulator

from fastapi.middleware.cors import CORSMiddleware

SIMULATOR = AerSimulator()

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
    is_eve: bool

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

def measure_bit(circuit, basis):
    """
    Measure a single qubit in a specified basis.

    Args:
        circuit (QuantumCircuit): The quantum circuit to be measured.
        basis (int): The measurement basis (0 for Z, 1 for X).

    Returns:
        int: The measured bit value (0 or 1).
    """
    qc = circuit.copy()
    if basis == 1:
        qc.h(0)
    qc.measure(0, 0)
    job = SIMULATOR.run(qc, shots=1)
    result = job.result().get_counts()
    measured_bit = int(list(result.keys())[0])
    return measured_bit

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

@app.post('/initialize_connection')
def initiliaze_connection(payload: FrontEndInitializePayload):
    """
    Initialize the BB84 QKD protocol simulation.

    This endpoint orchestrates the entire QKD flow:
    1. Generates random bits and bases for Alice.
    2. Encodes Alice's bits into quantum states (qubits as QASM strings).
    3. Simulates Eve's interception if 'is_eve' is enabled (measuring and re-encoding).
    4. Sends the qubits to Bob's server over the classical-quantum simulated channel.
    5. Retrieves Bob's measurement bases to sift the key.
    6. Identifies matching bases (sifting process).
    7. Sends a 20% sample of sifted bits to Bob to check QBER (Quantum Bit Error Rate).
    8. If QBER > 11%, aborts. Otherwise, derives the final key and encrypts a test message.
    """
    alice_bits, alice_bases = generate_bits_and_base(payload.num_bits)

    qasm_strings = []
    eve_bases = []
    eve_measured_bits = []
    for i in range(payload.num_bits):
        qc = encode_bit(alice_bits[i], alice_bases[i])
        qasm_strings.append(qasm2.dumps(qc))
    if payload.is_eve == True:
        _, eve_created_bases = generate_bits_and_base(payload.num_bits)
        eve_bases = eve_created_bases
        harmful_qasm_strings = []
        
        for i, qasm_str in enumerate(qasm_strings):
            qc = qasm2.loads(qasm_str)
            measured_bit = measure_bit(qc, eve_bases[i])
            eve_measured_bits.append(measured_bit)
        for i in range(len(eve_measured_bits)):
            qc = encode_bit(eve_measured_bits[i], eve_bases[i])
            harmful_qasm_strings.append(qasm2.dumps(qc))
        qasm_strings = harmful_qasm_strings

    print("Sending Qubits over Quantum Channel (HTTP POST)...")
    res = requests.post(f"{SERVER_URL}/quantum_channel/receive", json={"qasm_strings": qasm_strings, "num_bits": payload.num_bits})
    print("Bob's response:", res.json())

    print("\n--- [2] SIFTING (Getting Bob's bases) ---")
    res = requests.get(f"{SERVER_URL}/classical_channel/bases")
    bob_bases = res.json()["bob_bases"]

    matching_indices = [i for i in range(payload.num_bits) if alice_bases[i] == bob_bases[i]]
    print(f"Number of bits with matching bases: {len(matching_indices)}")

    print("\n--- [3] QBER VERIFICATION ---")
    sample_size = int(len(matching_indices) * 0.2)
    sample_indices = random.sample(matching_indices, sample_size)
    sample_bits = [alice_bits[i] for i in sample_indices]

    print("Sending QBER test sample to Bob (HTTP POST)...")
    res = requests.post(
        f"{SERVER_URL}/classical_channel/check_qber", 
        json={"sample_indices": sample_indices, "sample_bits": sample_bits, "matching_indices": matching_indices}
    )
    qber = res.json()["qber"]
    bob_measured_bits_from_bob = res.json()["bob_measured_bits"]
    mismatches = res.json().get("mismatches", 0)
    print(f"QBER calculated by Bob: {qber * 100}%")

    if qber > 0.11:
        print("❌ Eavesdropper detected, aborting key!")
        return {
            "initial_alice_bits": alice_bits,
            "initial_alice_bases": alice_bases,
            "eve_bases": eve_bases,
            "eve_measured_bits": eve_measured_bits,
            "initial_bob_bases": bob_bases,
            "initial_bob_bits": bob_measured_bits_from_bob,
            "matching_indices_alice_bob": matching_indices,
            "sample_size_qber": sample_size,
            "sample_indices_qber": sample_indices,
            "sample_bits_qber": sample_bits,
            "qber": qber
        }
    else:
        print("✅ Channel is secure! Generating Final Key.")
        final_key = "".join([str(alice_bits[i]) for i in matching_indices if i not in sample_indices])
        print(f"Alice's Key: {final_key[:40]}...")

    print("\n--- [4] KEY APPLICATION (ENCRYPTING MESSAGE) ---")
    secret_message = "The secret base coordinates are: 10.762, 106.681. Do not share with anyone!"
    print(f"Original message: '{secret_message}'")

    # 1. Convert the binary final_key to an AES key (Fernet)
    key_hash = hashlib.sha256(final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)

    # 2. Encrypt the message
    encrypted_bytes = cipher.encrypt(secret_message.encode())
    encrypted_message = encrypted_bytes.decode()

    print(f"Message encrypted to: {encrypted_message[:50]}...")

    # 3. Send the encrypted message over the public network (HTTP POST)
    print("Sending over the Internet to Bob...")
    res = requests.post(
        f"{SERVER_URL}/chat/receive",
        json={
            "encrypted_message": encrypted_message,
            "bob_final_key_string": final_key  # Simulate Bob using the same key as Alice
        }
    )
    bob_final_key = res.json()["bob_final_key"]

    return {
        "initial_alice_bits": alice_bits,
        "initial_alice_bases": alice_bases,
        "eve_bases": eve_bases,
        "eve_measured_bits": eve_measured_bits,
        "initial_bob_bases": bob_bases,
        "initial_bob_bits": bob_measured_bits_from_bob,
        "matching_indices_alice_bob": matching_indices,
        "sample_size_qber": sample_size,
        "sample_indices_qber": sample_indices,
        "sample_bits_qber": sample_bits,
        "mismatches": mismatches, 
        "qber": qber,
        "alice_final_key": final_key,
        "bob_final_key": bob_final_key
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

