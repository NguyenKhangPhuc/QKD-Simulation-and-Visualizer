# BB84 Quantum Key Distribution Simulation

A FastAPI-based simulation of the BB84 Quantum Key Distribution (QKD) protocol implemented using Qiskit. The project simulates a quantum channel and a classical communication channel between two parties (Alice and Bob), with optional eavesdropping (Eve) detection.

## Features & Capabilities

- Quantum Qubit Encoding and Measurement: Uses Qiskit to create single-qubit circuits encoded in computational (Z) or diagonal (X) bases and serializes quantum circuits via OpenQASM 2.0.
- Classical Sifting & QBER Estimation: Compares basis choices over HTTP and samples key bits to calculate Quantum Bit Error Rate (QBER) to detect eavesdropping.
- Eavesdropping Simulation: Models an eavesdropper (Eve) intercepting, measuring, and re-transmitting qubits, leading to elevated QBER values (> 11%).
- Symmetric Encryption: Generates a shared secret key upon successful QKD to encrypt and decrypt classical messages using Fernet (AES-128).
- Independent Microservices: Alice client and Bob server run as separate FastAPI services on distinct ports.

## Tech Stack / Prerequisites

| Technology | Purpose |
| --- | --- |
| Python 3.9+ | Runtime environment |
| FastAPI | Web framework for API endpoints |
| Uvicorn | ASGI server implementation |
| Qiskit / Qiskit Aer | Quantum circuit construction and simulation |
| Cryptography | Fernet (AES) symmetric message encryption |
| Requests | HTTP client for inter-service communication |
| Pydantic | Data validation and payload modeling |

## Installation & Setup Instructions

1. Clone or navigate to the project directory:
   ```bash
   cd /home/nguyenkhangphuc/Projects/quantum-computing
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install fastapi uvicorn qiskit qiskit-aer cryptography requests pydantic
   ```

## Usage Examples / API Endpoints

### Running the Services

1. Start the Bob Server (Listens on localhost:8000):
   ```bash
   python3 bob_server.py
   ```

2. Start the Alice Client Server (Listens on localhost:8001):
   ```bash
   python3 alice_client.py
   ```

### API Endpoints

#### Bob Server (localhost:8000)

- POST `/quantum_channel/receive`
  - Accepts OpenQASM 2.0 serialized qubit circuits from Alice.
  - Measures received qubits using Bob's randomly generated measurement bases.

- GET `/classical_channel/bases`
  - Returns Bob's measurement bases to Alice for key sifting.

- POST `/classical_channel/check_qber`
  - Accepts sampled indices and bits from Alice, calculates the QBER, and establishes Bob's final key if QBER <= 11%.

- POST `/chat/receive`
  - Receives Fernet-encrypted ciphertext from Alice and decrypts it using the established BB84 shared secret key.

#### Alice Client (localhost:8001)

- POST `/initialize_connection`
  - Triggers the complete BB84 protocol sequence: qubit generation, transmission over quantum channel, basis sifting, QBER verification, key generation, and encrypted message transmission.
  - Accepts payload parameters:
    - `num_bits` (int): Number of quantum bits to generate.
    - `is_eve` (bool): Flag to enable or disable eavesdropping simulation.

### Triggering a Simulation Run

To trigger the BB84 protocol via Alice's endpoint without Eve:
```bash
curl -X POST "http://localhost:8001/initialize_connection" \
     -H "Content-Type: application/json" \
     -d '{"num_bits": 500, "is_eve": false}'
```

To trigger the BB84 protocol with Eve eavesdropping:
```bash
curl -X POST "http://localhost:8001/initialize_connection" \
     -H "Content-Type: application/json" \
     -d '{"num_bits": 500, "is_eve": true}'
```

## License

MIT License
