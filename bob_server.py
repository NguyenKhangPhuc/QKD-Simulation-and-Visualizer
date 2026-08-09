"""
Bob Server for BB84 Quantum Key Distribution (QKD) Protocol.

This script acts as the Bob receiver server. It exposes FastAPI endpoints representing 
simulated quantum and classical communication channels. It receives qubits (QASM), 
measures them using randomly chosen bases, participates in sifting, computes QBER 
classically, derives Bob's copy of the key, and decrypts secret messages sent by Alice.
"""

import random
from fastapi import FastAPI, Body
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import qiskit.qasm2 as qasm2  # Library to parse QASM strings
import hashlib
import base64
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

simulator = AerSimulator()

# Bob's internal state
NUM_BITS = 500
bob_bases = [random.randint(0, 1) for _ in range(NUM_BITS)]
bob_measured_bits = []

bob_final_key = None

# Definition of message payloads (Pydantic Models)
class QubitPayload(BaseModel):
    qasm_strings: list[str]  # List of QASM string representations of qubits

class QberPayload(BaseModel):
    sample_indices: list[int]
    sample_bits: list[int]
    matching_indices: list[int]

@app.post("/quantum_channel/receive")
def receive_qubits(payload: QubitPayload):
    """
    Quantum Channel Endpoint.
    
    Receives QASM strings representing qubits from Alice, reconstructs the
    QuantumCircuit objects, and simulates measurement using Bob's randomly
    generated bases. The measurement outcomes are saved in Bob's internal state.
    """
    global bob_measured_bits
    bob_measured_bits = []
    
    for i, qasm_str in enumerate(payload.qasm_strings):
        # 1. Reconstruct the QuantumCircuit from QASM string
        qc = qasm2.loads(qasm_str)
        
        # 2. Bob measures in his chosen basis
        if bob_bases[i] == 1: 
            qc.h(0)   
        qc.measure(0, 0)
        
        result = simulator.run(qc, shots=1).result().get_counts()
        bit = int(list(result.keys())[0])
        bob_measured_bits.append(bit)
        
    return {"status": "success", "message": f"Successfully measured {len(bob_measured_bits)} qubits"}

@app.get("/classical_channel/bases")
def get_bob_bases():
    """
    Classical Channel Endpoint.
    
    Allows Alice to fetch Bob's randomly chosen bases to perform key sifting.
    """
    return {"bob_bases": bob_bases}

@app.post("/classical_channel/check_qber")
def check_qber(payload: QberPayload):
    """
    Classical Channel Endpoint.
    
    Receives a test sample from Alice, compares Bob's measurement outcomes
    with Alice's original bits, calculates the QBER (Quantum Bit Error Rate),
    and derives the final key if the error rate is under the 11% threshold.
    """
    mismatches = 0
    total_sample = len(payload.sample_indices)
    
    for i in range(total_sample):
        idx = payload.sample_indices[i]
        if payload.sample_bits[i] != bob_measured_bits[idx]:
            mismatches += 1
    
    qber = mismatches / total_sample
    if qber <= 0.11:
        # If secure, Bob derives his final key and stores it in RAM
        global bob_final_key
        bob_final_key = "".join([
            str(bob_measured_bits[i]) 
            for i in payload.matching_indices 
            if i not in payload.sample_indices
        ])
    return {"qber": qber, "bob_measured_bits": bob_measured_bits, "mismatches": mismatches}

@app.post("/chat/receive")
def receive_secret_message(
    encrypted_message: str = Body(..., embed=True), 
):
    """
    Classical Channel Endpoint.
    
    Receives the AES-encrypted message from Alice and attempts to decrypt it 
    using the established final QKD key. Returns the decrypted message or an error.
    """
    global bob_final_key
    print(bob_final_key)
    if not bob_final_key:
        return {"error": "Bob does not have a key to decrypt!"}
        
    # 1. Convert Bob's binary key to an AES key (Fernet)
    key_hash = hashlib.sha256(bob_final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)
    
    try:
        # 2. Decrypt the message
        decrypted_bytes = cipher.decrypt(encrypted_message.encode())
        plain_text = decrypted_bytes.decode()
        
        print(f"\n[Bob's Screen] 📩 Message decrypted successfully: {plain_text}")
        return {"status": "success", "decrypted_message": plain_text, "bob_final_key": bob_final_key}
        
    except Exception as e:
        return {"status": "error", "message": "Decryption failed! Key mismatch."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)