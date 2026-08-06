import random
import requests
from qiskit import QuantumCircuit
import qiskit.qasm2 as qasm2
import hashlib
import base64
from cryptography.fernet import Fernet
from fastapi import FastAPI,Body
from pydantic import BaseModel
from qiskit_aer import AerSimulator

SIMULATOR = AerSimulator()

SERVER_URL = "http://localhost:8000"
NUM_BITS = 500
app = FastAPI()

print("--- [1] KHỞI TẠO VÀ MÃ HÓA QUBITS ---")

class FrontEndInitializePayload(BaseModel):
    num_bits: int
    is_eve: bool

def generate_bits_and_base(num_bits: int):
    bits = [random.randint(0, 1) for _ in range(payload.num_bits)]
    bases = [random.randint(0, 1) for _ in range(payload.num_bits)]
    return bits,bases

def measure_bit(circuit, basis):
    qc = circuit.copy()
    if (basis == 1):
        qc.h(0,0)
    job = SIMULATOR.run(qc, shots=1)
    result = job.result().get_counts()
    measured_bit = int(list(result.keys())[0])
    return measured_bit

def encode_bit( bit, base):
    qc = QuantumCircuit(1, 1)
    if (bit == 1):
        qc.x(0)
    
    if (base == 1):
        qc.h(0)
    
    return qc

@app.post('/initialize_connection')
def initiliaze_connection(payload: FrontEndInitializePayload):
    alice_bits,alice_bases = generate_bits_and_base(payload.num_bits)

    qasm_strings = []
    for i in range(NUM_BITS):
        qc = encode_bit(alice_bits[i], alice_bases[i])
        qasm_strings.append(qasm2.dumps(qc))
    if payload.is_eve == True:
        _, eve_bases = generate_bits_and_base(payload.num_bits)
        harmful_qasm_strings = []
        eve_measured_bits = []
        for i, qasm_str in enumerate(qasm_strings):
            qc = qasm2.load(qasm_str)
            measured_bit = measure_bit(qc, eve_bases[i])
            eve_measured_bits.append(measured_bit)
        for i in range(len(eve_measured_bits)):
            qc = encode_bit(eve_measured_bits[i], eve_bases[i])
            harmful_qasm_strings.append(qasm2.dumps(qc))
        qasm_strings = harmful_qasm_strings

    print("Gửi Qubits qua Quantum Channel (HTTP POST)...")
    res = requests.post(f"{SERVER_URL}/quantum_channel/receive", json={"qasm_strings": qasm_strings})
    print("Bob phản hồi:", res.json())

    print("\n--- [2] SIFTING (Lấy bases của Bob) ---")
    res = requests.get(f"{SERVER_URL}/classical_channel/bases")
    bob_bases = res.json()["bob_bases"]

    matching_indices = [i for i in range(NUM_BITS) if alice_bases[i] == bob_bases[i]]
    print(f"Số lượng bit khớp cơ sở: {len(matching_indices)}")

    print("\n--- [3] KIỂM TRA QBER ---")
    sample_size = int(len(matching_indices) * 0.2)
    sample_indices = random.sample(matching_indices, sample_size)
    sample_bits = [alice_bits[i] for i in sample_indices]

    print("Gửi bài test QBER cho Bob (HTTP POST)...")
    res = requests.post(
        f"{SERVER_URL}/classical_channel/check_qber", 
        json={"sample_indices": sample_indices, "sample_bits": sample_bits, "matching_indices": matching_indices}
    )
    qber = res.json()["qber"]
    print(f"QBER do Bob tính toán: {qber * 100}%")

    if qber > 0.11:
        print("❌ Bị nghe lén, hủy khóa!")
    else:
        print("✅ Mạng an toàn! Tạo Final Key.")
        final_key = "".join([str(alice_bits[i]) for i in matching_indices if i not in sample_indices])
        print(f"Alice Key: {final_key[:40]}...")

    print("\n--- [4] ỨNG DỤNG KHÓA (MÃ HÓA TIN NHẮN) ---")
    secret_message = "Tọa độ căn cứ bí mật là: 10.762, 106.681. Đừng nói cho ai biết!"
    print(f"Tin nhắn gốc: '{secret_message}'")

    # 1. Biến chuỗi nhị phân final_key thành chìa khóa AES (Fernet)
    key_hash = hashlib.sha256(final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)

    # 2. Mã hóa tin nhắn
    encrypted_bytes = cipher.encrypt(secret_message.encode())
    encrypted_message = encrypted_bytes.decode()

    print(f"Tin nhắn đã bị mã hóa thành: {encrypted_message[:50]}...")

    # 3. Gửi tin nhắn mã hóa qua mạng công cộng (HTTP POST)
    print("Đang gửi qua Internet cho Bob...")
    res = requests.post(
        f"{SERVER_URL}/chat/receive",
        json={
            "encrypted_message": encrypted_message,
            "bob_final_key_string": final_key  # Giả lập Bob dùng key giống Alice
        }
    )

    print("Kết quả từ Bob:", res.json())