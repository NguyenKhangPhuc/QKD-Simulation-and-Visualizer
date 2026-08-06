import random
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

simulator = AerSimulator()

# =====================================================================
# 1. QUANTUM CHANNEL (Kênh truyền hạt Photon & Kẻ nghe lén)
# =====================================================================
class Quantum_Channel:
    """
    Kênh truyền lượng tử đóng vai trò như sợi cáp quang dẫn photon.
    
    Attributes:
        eve_present (bool): Cờ (flag) xác định xem kẻ nghe lén (Eve) 
                            có đang can thiệp vào đường truyền hay không.
                            True: Có nghe lén, False: Môi trường an toàn.
    """
    def __init__(self, eve_present=False):
        self.eve_present = eve_present

    def transmit(self, qubits):
        """
        Mô phỏng quá trình truyền photon. Nếu có Eve, Eve sẽ can thiệp vào 'qubits'.
        
        Args:
            qubits (list[QuantumCircuit]): Danh sách các photon do Alice gửi đi.
            
        Returns:
            list[QuantumCircuit]: Danh sách photon truyền tới tay Bob 
                                  (có thể là hàng thật, hoặc hàng giả do Eve tạo lại).
        """
        if not self.eve_present:
            return qubits

        print("⚠️ [Quantum Channel] Eve đang can thiệp vào đường truyền!")
        
        # eve_fake_qubits: Lưu các photon MỚI do Eve tạo ra để lừa Bob
        eve_fake_qubits = [] 
        num_bits = len(qubits)
        
        # eve_bases: Cơ sở đo ngẫu nhiên mà Eve dùng để đo lén (0: Z, 1: X)
        eve_bases = [random.randint(0, 1) for _ in range(num_bits)]
        
        for i in range(num_bits):
            qc = qubits[i].copy()
            if eve_bases[i] == 1:
                qc.h(0)
            qc.measure(0, 0)
            
            result = simulator.run(qc, shots=1).result().get_counts()
            
            # eve_bit: Giá trị bit (0 hoặc 1) mà Eve đo lén được
            eve_bit = int(list(result.keys())[0])
            
            fake_qc = QuantumCircuit(1, 1)
            if eve_bit == 1: fake_qc.x(0)
            if eve_bases[i] == 1: fake_qc.h(0)
            
            eve_fake_qubits.append(fake_qc)
            
        return eve_fake_qubits


# =====================================================================
# 2. BROADCAST CHANNEL (Kênh Cổ Điển)
# =====================================================================
class BroadcastChannel:
    """
    Kênh công cộng mô phỏng Internet/Wifi. Ai cũng có thể đọc được dữ liệu ở đây.
    
    Attributes:
        data_store (dict): Bộ nhớ dạng từ điển đóng vai trò như một bảng tin công cộng. 
                           Lưu dữ liệu với cấu trúc { "Tên_chủ_đề": [Dữ_liệu] }.
    """
    def __init__(self):
        self.data_store = {}

    def send(self, topic, data):
        self.data_store[topic] = data

    def receive(self, topic):
        return self.data_store.get(topic, None)


# =====================================================================
# 3. CLASS ALICE (Người Gửi)
# =====================================================================
class Alice:
    """
    Người khởi tạo giao thức BB84.
    
    Attributes:
        num_bits (int): Số lượng photon ban đầu Alice muốn gửi đi.
        my_bits (list[int]): Sổ tay TUYỆT MẬT lưu các bit (0/1) ngẫu nhiên của Alice.
        my_bases (list[int]): Sổ tay TUYỆT MẬT lưu cơ sở đo (0/1) dùng để mã hóa của Alice.
        matching_indices (list[int]): Lưu các CHỈ SỐ (vị trí) mà Alice và Bob dùng trùng cơ sở đo.
        sample_indices (list[int]): Lưu các CHỈ SỐ bốc thăm ngẫu nhiên để công khai tính QBER.
    """
    def __init__(self, num_bits):
        self.num_bits = num_bits
        self.my_bits = [random.randint(0, 1) for _ in range(num_bits)]
        self.my_bases = [random.randint(0, 1) for _ in range(num_bits)]
        self.matching_indices = []
        self.sample_indices = []

    def create_and_send_qubits(self, quantum_channel):
        """Mã hóa my_bits và my_bases thành Qubits."""
        # qubits: Biến cục bộ lưu mảng các QuantumCircuit để ném vào đường truyền
        qubits = []
        for i in range(self.num_bits):
            qc = QuantumCircuit(1, 1)
            if self.my_bits[i] == 1: qc.x(0)
            if self.my_bases[i] == 1: qc.h(0)
            qubits.append(qc)
        
        return quantum_channel.transmit(qubits)

    def announce_bases(self, broadcast_channel):
        broadcast_channel.send("alice_bases", self.my_bases)

    def find_matching_bases(self, broadcast_channel):
        # bob_bases: Dữ liệu tải về từ kênh công cộng chứa cơ sở đo của Bob
        bob_bases = broadcast_channel.receive("bob_bases")
        self.matching_indices = [
            i for i in range(self.num_bits) if self.my_bases[i] == bob_bases[i]
        ]
        broadcast_channel.send("matching_indices", self.matching_indices)

    def send_qber_sample(self, broadcast_channel):
        # sample_size: Số lượng bit chiếm 20% mảng matching_indices
        sample_size = int(len(self.matching_indices) * 0.2)
        self.sample_indices = random.sample(self.matching_indices, sample_size)
        
        # sample_bits: Giá trị 0/1 thực tế tương ứng với các vị trí bốc thăm
        sample_bits = [self.my_bits[i] for i in self.sample_indices]
        
        broadcast_channel.send("alice_sample_indices", self.sample_indices)
        broadcast_channel.send("alice_sample_bits", sample_bits)

    def make_final_key(self):
        # final_key: Chuỗi khóa bí mật cuối cùng dạng String (vd: "10011")
        final_key = [str(self.my_bits[i]) for i in self.matching_indices if i not in self.sample_indices]
        return "".join(final_key)


# =====================================================================
# 4. CLASS BOB (Người Nhận & Đo QBER)
# =====================================================================
class Bob:
    """
    Người nhận và đo lường Qubit.
    
    Attributes:
        num_bits (int): Số lượng photon mong đợi nhận được.
        my_bases (list[int]): Sổ tay TUYỆT MẬT chứa các cơ sở đo ngẫu nhiên Bob tự chọn.
        measured_bits (list[int]): Dữ liệu TUYỆT MẬT chứa kết quả Bob đọc được sau khi đo photon.
    """
    def __init__(self, num_bits):
        self.num_bits = num_bits
        self.my_bases = [random.randint(0, 1) for _ in range(num_bits)]
        self.measured_bits = []

    def measure_qubits(self, received_qubits):
        for i in range(self.num_bits):
            qc = received_qubits[i].copy()
            if self.my_bases[i] == 1: qc.h(0)
            qc.measure(0, 0)
            
            # result: Kết quả trả về từ Simulator dưới dạng Dictionary (vd: {'1': 1})
            result = simulator.run(qc, shots=1).result().get_counts()
            
            # bit: Tách lấy con số 0 hoặc 1 từ Dictionary trên
            bit = int(list(result.keys())[0])
            self.measured_bits.append(bit)

    def announce_bases(self, broadcast_channel):
        broadcast_channel.send("bob_bases", self.my_bases)

    def calculate_qber(self, broadcast_channel):
        # alice_sample_indices: Danh sách bài tập (chỉ số) Alice giao cho Bob check
        alice_sample_indices = broadcast_channel.receive("alice_sample_indices")
        # alice_sample_bits: Đáp án của Alice để Bob tự chấm điểm
        alice_sample_bits = broadcast_channel.receive("alice_sample_bits")
        
        # mismatches: Bộ đếm số lần Bob đo ra kết quả khác với đáp án của Alice
        mismatches = 0
        total_sample = len(alice_sample_indices)
        
        for i in range(total_sample):
            idx = alice_sample_indices[i]
            if alice_sample_bits[i] != self.measured_bits[idx]:
                mismatches += 1
                
        # qber: Quantum Bit Error Rate (Tỷ lệ lỗi)
        qber = mismatches / total_sample
        return qber

    def make_final_key(self, broadcast_channel):
        matching_indices = broadcast_channel.receive("matching_indices")
        alice_sample_indices = broadcast_channel.receive("alice_sample_indices")
        
        final_key = [str(self.measured_bits[i]) for i in matching_indices if i not in alice_sample_indices]
        return "".join(final_key)

# =====================================================================
def start_bb84_session(eve_present=False):
    num_bits = 1000
    
    # Khởi tạo các thành phần mạng và người dùng
    q_channel = Quantum_Channel(eve_present=eve_present)
    c_channel = BroadcastChannel()
    alice = Alice(num_bits)
    bob = Bob(num_bits)
    
    print("\n--- [1] TRUYỀN TẢI LƯỢNG TỬ ---")
    qubits_on_fly = alice.create_and_send_qubits(q_channel)
    bob.measure_qubits(qubits_on_fly)
    
    print("--- [2] GIAO TIẾP CỔ ĐIỂN (SIFTING) ---")
    alice.announce_bases(c_channel)
    bob.announce_bases(c_channel)
    alice.find_matching_bases(c_channel)  # Alice tính toán và đẩy matching_indices lên kênh
    
    print("--- [3] KIỂM TRA NGHE LÉN (QBER) ---")
    alice.send_qber_sample(c_channel)
    
    # Do Bob phụ trách tính QBER theo yêu cầu
    qber = bob.calculate_qber(c_channel)
    print(f"Bob báo cáo QBER: {qber * 100:.1f}%")
    
    if qber > 0.11:
        print("❌ Kênh bị thỏa hiệp! Dừng giao thức.")
        return
        
    print("--- [4] TẠO KHÓA BÍ MẬT ---")
    alice_key = alice.make_final_key()
    bob_key = bob.make_final_key(c_channel)
    
    print(f"Alice Key : {alice_key[:40]}...")
    print(f"Bob Key   : {bob_key[:40]}...")
    print(f"Khớp nhau : {'CÓ ✅' if alice_key == bob_key else 'KHÔNG ❌'}")

if __name__ == "__main__":
    print("======== TRƯỜNG HỢP 1: KHÔNG CÓ EVE ========")
    start_bb84_session(eve_present=False)
    
    print("\n======== TRƯỜNG HỢP 2: CÓ EVE NGHE LÉN ========")
    start_bb84_session(eve_present=True)