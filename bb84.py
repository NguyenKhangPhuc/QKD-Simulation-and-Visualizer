import random
import hashlib
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Kho chứa thiết bị mô phỏng lượng tử
SIMULATOR = AerSimulator()

# -------------------------------------------------------------------
# 1. Các hàm xử lý Lượng tử (Quantum Logic)
# -------------------------------------------------------------------

def generate_bits_and_bases(n):
    """Sinh ngẫu nhiên chuỗi bits và cơ sở đo (bases) cho Alice/Bob"""
    bits = [random.randint(0, 1) for _ in range(n)]
    bases = [random.randint(0, 1) for _ in range(n)] # 0: Z-basis, 1: X-basis
    return bits, bases

def encode_qubit(bit, basis):
    """Encode 1 bit cổ điển thành 1 QuantumCircuit (qubit)"""
    qc = QuantumCircuit(1, 1)
    
    # Đưa qubit về bit mong muốn (nếu bit = 1 thì áp dụng cổng X)
    if bit == 1:
        qc.x(0)
        
    # Nếu chọn X-basis (basis = 1), áp dụng cổng Hadamard (H)
    if basis == 1:
        qc.h(0)
        
    return qc

def measure_qubit(circuit, basis):
    """Đo 1 qubit theo cơ sở (basis) chỉ định"""
    # Tạo bản sao mạch để không làm hỏng mạch gốc
    qc = circuit.copy()
    
    # Nếu người đo dùng X-basis (basis = 1), xoay lại cơ sở bằng cổng H trước khi đo
    if basis == 1:
        qc.h(0)
        
    qc.measure(0, 0)
    
    # Chạy mô phỏng 1 lần đo (shots=1)
    job = SIMULATOR.run(qc, shots=1)
    result = job.result().get_counts()
    measured_bit = int(list(result.keys())[0])
    return measured_bit

# -------------------------------------------------------------------
# 2. Các hàm xử lý Kênh Cổ điển & Thuật toán Kỹ thuật (Classical Logic)
# -------------------------------------------------------------------

def intercept_eve(qubits, eve_bases):
    """Giả lập Kẻ nghe lén (Eve) chặn đường truyền và đo lén"""
    intercepted_qubits = []
    for qc, eve_basis in zip(qubits, eve_bases):
        # Eve đo qubit của Alice
        measured_bit = measure_qubit(qc, eve_basis)
        # Eve buộc phải tạo lại 1 qubit mới dựa trên kết quả vừa đo để gửi cho Bob
        new_qc = encode_qubit(measured_bit, eve_basis)
        intercepted_qubits.append(new_qc)
    return intercepted_qubits

def sift_key(alice_bases, bob_bases, alice_bits, bob_bits):
    """Lọc khóa (Sifting): Chỉ giữ lại các bit tại vị trí Alice và Bob trùng Basis"""
    sifted_alice = []
    sifted_bob = []
    sifted_indices = []
    
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])
            sifted_indices.append(i)
            
    return sifted_alice, sifted_bob, sifted_indices

def calculate_qber(sifted_alice, sifted_bob, sample_fraction=0.2):
    """Hy sinh a fraction % số bit để tính tỷ lệ lỗi QBER"""
    n = len(sifted_alice)
    if n == 0:
        return 1.0, [], [], []
        
    sample_size = max(1, int(n * sample_fraction))
    sample_indices = random.sample(range(n), sample_size)
    
    mismatches = 0
    for idx in sample_indices:
        if sifted_alice[idx] != sifted_bob[idx]:
            mismatches += 1
            
    qber = mismatches / sample_size
    
    # Giữ lại phần bit KHÔNG bị lấy mẫu kiểm tra
    checked_set = set(sample_indices)
    remaining_alice = [sifted_alice[i] for i in range(n) if i not in checked_set]
    remaining_bob = [sifted_bob[i] for i in range(n) if i not in checked_set]
    
    return qber, remaining_alice, remaining_bob

def privacy_amplification(bit_list):
    """Rút gọn chuỗi bit thành Key cố định bằng SHA-256 (Hash)"""
    bit_string = "".join(map(str, bit_list))
    hashed_key = hashlib.sha256(bit_string.encode()).hexdigest()
    return hashed_key

# -------------------------------------------------------------------
# 3. Luồng chạy thử nghiệm chính (Main Workflow)
# -------------------------------------------------------------------

def run_bb84_simulation(num_bits=1000, enable_eve=False):
    print(f"\n=================== CHẠY BB84 (Eve Present = {enable_eve}) ===================")
    
    # Step 1: Alice khởi tạo bits và bases
    alice_bits, alice_bases = generate_bits_and_bases(num_bits)
    alice_qubits = [encode_qubit(b, base) for b, base in zip(alice_bits, alice_bases)]
    
    # Step 2: Kênh lượng tử (Có Eve hoặc Không có Eve)
    if enable_eve:
        _, eve_bases = generate_bits_and_bases(num_bits)
        bob_received_qubits = intercept_eve(alice_qubits, eve_bases)
    else:
        bob_received_qubits = alice_qubits # Photon đi thẳng tới Bob
        
    # Step 3: Bob chọn bases ngẫu nhiên và đo
    _, bob_bases = generate_bits_and_bases(num_bits)
    bob_bits = [measure_qubit(qc, base) for qc, base in zip(bob_received_qubits, bob_bases)]
    
    # Step 4: Sifting (Lọc cơ sở trên kênh cổ điển)
    sifted_alice, sifted_bob, _ = sift_key(alice_bases, bob_bases, alice_bits, bob_bits)
    print(f"Tổng số bit ban đầu: {num_bits}")
    print(f"Số bit còn lại sau Sifting: {len(sifted_alice)} (~50%)")
    
    # Step 5: Tính QBER
    qber, remaining_alice, remaining_bob = calculate_qber(sifted_alice, sifted_bob, sample_fraction=0.2)
    print(f"QBER Ước lượng: {qber * 100:.2f}%")
    
    # Step 6: Đánh giá an toàn & Privacy Amplification
    THRESHOLD = 0.11 # Ngưỡng 11%
    if qber > THRESHOLD:
        print("⚠️ QBER VƯỢT NGƯỠNG (Có kẻ nghe lén!) -> HỦY BỎ KHÓA")
        return None, None
    else:
        alice_final_key = privacy_amplification(remaining_alice)
        bob_final_key = privacy_amplification(remaining_bob)
        
        print("✓ An toàn! Đã tạo Final Key.")
        print(f"Alice Key: {alice_final_key}")
        print(f"Bob Key  : {bob_final_key}")
        print(f"Khóa khớp 100%: {alice_final_key == bob_final_key}")
        return alice_final_key, bob_final_key

# --- CHẠY THỬ 2 TRƯỜNG HỢP ---
if __name__ == "__main__":
    # Trường hợp 1: Không có Eve (An toàn)
    run_bb84_simulation(num_bits=1000, enable_eve=False)
    
    # Trường hợp 2: Có Eve đo lén (Phát hiện lỗi)
    run_bb84_simulation(num_bits=1000, enable_eve=True)