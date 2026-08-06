import random
from fastapi import FastAPI,Body
from pydantic import BaseModel
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import qiskit.qasm2 as qasm2  # Thư viện để dịch chuỗi QASM
import hashlib
import base64
from cryptography.fernet import Fernet
app = FastAPI()
simulator = AerSimulator()

# Dữ liệu nội bộ của Bob
NUM_BITS = 500
bob_bases = [random.randint(0, 1) for _ in range(NUM_BITS)]
bob_measured_bits = []

bob_final_key = None

# Định nghĩa cấu trúc gói tin (Payload)
class QubitPayload(BaseModel):
    qasm_strings: list[str]  # Chứa danh sách các chuỗi QASM

class QberPayload(BaseModel):
    sample_indices: list[int]
    sample_bits: list[int]
    matching_indices: list[int]

@app.post("/quantum_channel/receive")
def receive_qubits(payload: QubitPayload):
    """KÊNH LƯỢNG TỬ: Nhận chuỗi QASM từ Alice, dựng lại Qubit và Đo"""
    global bob_measured_bits
    bob_measured_bits = []
    
    for i, qasm_str in enumerate(payload.qasm_strings):
        # 1. Dựng lại QuantumCircuit từ chuỗi QASM
        qc = qasm2.loads(qasm_str)
        
        # 2. Bob đo theo cơ sở của mình
        if bob_bases[i] == 1: qc.h(0)   
        qc.measure(0, 0)
        
        result = simulator.run(qc, shots=1).result().get_counts()
        bit = int(list(result.keys())[0])
        bob_measured_bits.append(bit)
        
    return {"status": "success", "message": f"Đã đo xong {len(bob_measured_bits)} qubits"}

@app.get("/classical_channel/bases")
def get_bob_bases():
    """KÊNH CỔ ĐIỂN: Alice gọi API này để lấy cơ sở đo của Bob"""
    return {"bob_bases": bob_bases}

@app.post("/classical_channel/check_qber")
def check_qber(payload: QberPayload):
    """KÊNH CỔ ĐIỂN: Alice gửi mẫu, Bob tính QBER và trả kết quả về"""
    mismatches = 0
    total_sample = len(payload.sample_indices)
    
    for i in range(total_sample):
        idx = payload.sample_indices[i]
        if payload.sample_bits[i] != bob_measured_bits[idx]:
            mismatches += 1
    
    qber = mismatches / total_sample
    if qber <= 0.11:
        # Nếu an toàn, BOB TỰ TÍNH FINAL KEY CỦA MÌNH VÀ LƯU VÀO RAM
        global bob_final_key
        bob_final_key = "".join([
            str(bob_measured_bits[i]) 
            for i in payload.matching_indices 
            if i not in payload.sample_indices
        ])
    return {"qber": qber}


@app.post("/chat/receive")
def receive_secret_message(
    encrypted_message: str = Body(..., embed=True), 
):
    """
    KÊNH CỔ ĐIỂN: Nhận tin nhắn đã mã hóa từ Alice và giải mã bằng Khóa BB84.
    (Lưu ý: Trong thực tế Bob tự giữ final_key của mình trong RAM, 
    ở đây ta truyền vào API cho dễ test luồng).
    """
    global bob_final_key
    print(bob_final_key)
    if not bob_final_key:
        return {"error": "Bob chưa có khóa để giải mã!"}
    # 1. Biến chuỗi nhị phân của Bob thành chìa khóa AES (Fernet)
    key_hash = hashlib.sha256(bob_final_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)
    
    try:
        # 2. Giải mã tin nhắn
        decrypted_bytes = cipher.decrypt(encrypted_message.encode())
        plain_text = decrypted_bytes.decode()
        
        print(f"\n[Bob's Screen] 📩 Tin nhắn giải mã thành công: {plain_text}")
        return {"status": "success", "decrypted_message": plain_text}
        
    except Exception as e:
        return {"status": "error", "message": "Giải mã thất bại! Khóa không khớp."}
# Lệnh chạy Server: uvicorn bob_server:app --reload