"""
Bob Server for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Bob receiver server. It exposes FastAPI endpoints representing
quantum and classical communication channels. It receives qubits (QASM), measures them
using randomly chosen bases, participates in sifting, computes QBER classically,
derives Bob's copy of the key, and decrypts secret messages sent by Alice.

Supports realistic channel noise: depolarization errors during measurement.
"""

import random
import hashlib
import base64
from fastapi import FastAPI, Body
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
import qiskit.qasm2 as qasm2
from cryptography.fernet import Fernet
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bob's internal state (dict-based to handle photon loss / index mismatch)
bob_bases = {}  # {photon_index: basis}
bob_measured_bits = {}  # {photon_index: measured_bit}
bob_final_key = None


class QubitPayload(BaseModel):
    qasm_strings: list[str]
    received_indices: list[int]
    depolarization_rate: float = 0.02


class QberPayload(BaseModel):
    sample_indices: list[int]
    sample_bits: list[int]
    matching_indices: list[int]


@app.post("/quantum_channel/receive")
def receive_qubits(payload: QubitPayload):
    """
    Quantum Channel Endpoint.

    Receives QASM strings representing qubits from Alice (only those that survived
    fiber attenuation), reconstructs the QuantumCircuit objects, and simulates
    measurement using Bob's randomly generated bases. Measurement results are stored
    in Bob's internal state as {photon_index: bit_value}.
    """
    global bob_bases, bob_measured_bits
    bob_measured_bits = {}
    bob_bases = {}

    # Build Qiskit Aer NoiseModel for measurement execution
    noise_model = NoiseModel()
    if payload.depolarization_rate > 0:
        error = depolarizing_error(payload.depolarization_rate, 1)
        noise_model.add_all_qubit_quantum_error(error, ["h", "x", "measure"])

    simulator = AerSimulator(noise_model=noise_model)

    for idx, qasm_str in zip(payload.received_indices, payload.qasm_strings):
        qc = qasm2.loads(qasm_str)

        # Bob chooses a random basis for this photon
        basis = random.randint(0, 1)
        bob_bases[idx] = basis

        # Apply Bob's chosen basis measurement
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
    Classical Channel Endpoint.

    Receives a test sample from Alice, compares Bob's measurement outcomes
    with Alice's original bits, calculates the QBER (Quantum Bit Error Rate),
    and derives Bob's final key if the error rate is under the 11% threshold.
    """
    mismatches = 0
    total_sample = len(payload.sample_indices)

    if total_sample == 0:
        return {"qber": 1.0, "mismatches": 0, "bob_measured_bits": bob_measured_bits}

    for i in range(total_sample):
        idx = payload.sample_indices[i]
        if payload.sample_bits[i] != bob_measured_bits.get(idx):
            mismatches += 1

    qber = mismatches / total_sample

    if qber <= 0.11:
        global bob_final_key
        bob_final_key = "".join(
            [
                str(bob_measured_bits[idx])
                for idx in payload.matching_indices
                if idx not in payload.sample_indices
            ]
        )

    return {"qber": qber, "bob_measured_bits": bob_measured_bits, "mismatches": mismatches}


@app.post("/chat/receive")
def receive_secret_message(encrypted_message: str = Body(..., embed=True)):
    """
    Classical Channel Endpoint.

    Receives the AES-encrypted message from Alice and attempts to decrypt it
    using the established final QKD key. Returns the decrypted message or an error.
    """
    global bob_final_key
    if not bob_final_key:
        return {"error": "Bob does not have a key to decrypt!"}

    # Convert Bob's binary key to an AES key (Fernet)
    key_hash = hashlib.sha256(bob_final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)

    try:
        # Decrypt the message
        decrypted_bytes = cipher.decrypt(encrypted_message.encode())
        plain_text = decrypted_bytes.decode()

        print(f"\n[Bob's Screen] 📩 Message decrypted successfully: {plain_text}")
        return {
            "status": "success",
            "decrypted_message": plain_text,
            "bob_final_key": bob_final_key,
        }

    except Exception as e:
        print(f"Return final key of bob {bob_final_key}")
        return {
            "status": "error",
            "message": "Decryption failed! Key mismatch.",
            "bob_final_key": bob_final_key,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
