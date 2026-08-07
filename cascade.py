"""
Cascade Protocol - Bản cài đặt theo đúng nguyên bản Brassard & Salvail (1994)
================================================================================
Bổ sung so với bản demo đơn giản ban đầu:
  1. Chọn block size vòng 1 theo công thức tối ưu: k1 = floor(0.73 / QBER)
     Các vòng sau: k_i = 2 * k_(i-1)  (nhân đôi mỗi vòng)
  2. BACKTRACKING (đây chính là lý do thuật toán tên là "Cascade" - hiệu ứng
     dây chuyền): mỗi khi sửa 1 bit ở vòng hiện tại, phải quay lại kiểm tra
     TẤT CẢ các khối ở CÁC VÒNG TRƯỚC có chứa vị trí đó, vì việc lật 1 bit có
     thể làm đổi parity của khối chứa nó ở vòng trước -> lộ ra thêm 1 lỗi nữa
     (do trước đó 2 lỗi cùng nằm 1 khối, parity chẵn nên "ẩn" nhau).
  3. Mô phỏng flow QKD đầy đủ: sifted key -> ước lượng QBER bằng mẫu công khai
     -> kiểm tra ngưỡng an toàn -> Cascade reconciliation -> Privacy Amplification.
"""

import math
import random


# ---------------------------------------------------------------------------
# ƯỚC LƯỢNG QBER AN TOÀN HƠN: Serfling bound (lấy mẫu không hoàn lại)
# ---------------------------------------------------------------------------

def serfling_upper_bound(sample_qber, n, m, epsilon):
    """
    Tính CẬN TRÊN của QBER thật (trên phần khóa CHƯA lấy mẫu) với độ tin cậy
    (1 - epsilon), dựa trên QBER đo được trên mẫu.

    Vấn đề của việc dùng thẳng `qber_estimate = sample_errors/sample_size`:
    đây chỉ là 1 điểm ước lượng, có thể lệch khá xa so với QBER thật của toàn
    bộ khóa chỉ vì may rủi khi chọn mẫu (như đã tính ở lượt trước: xác suất
    mẫu bắt được 0 lỗi dù thực tế có lỗi là ~34% với mẫu nhỏ).

    Serfling's inequality (1974) cho lấy mẫu KHÔNG HOÀN LẠI từ 1 quần thể hữu
    hạn kích thước n, với mẫu kích thước m và trung bình mẫu `sample_qber`:

        P( qber_that_su - sample_qber >= delta ) <= exp( -2*m*delta^2 / (1 - (m-1)/n) )

    Giải ngược để tìm delta ứng với 1 xác suất thất bại mong muốn `epsilon`:

        delta = sqrt( ln(1/epsilon) * (1 - (m-1)/n) / (2*m) )

    Cận trên trả về: sample_qber + delta. Với xác suất >= (1-epsilon),
    QBER thật KHÔNG vượt quá giá trị này -> dùng giá trị này để quyết định
    thay vì dùng thẳng sample_qber, giúp tránh trường hợp mẫu "may mắn" đo
    ra QBER thấp hơn thực tế mà vẫn tưởng an toàn.
    """
    m = max(1, m)
    finite_population_factor = max(0.0, 1 - (m - 1) / n)
    delta = math.sqrt(math.log(1 / epsilon) * finite_population_factor / (2 * m))
    return min(1.0, sample_qber + delta)


# ---------------------------------------------------------------------------
# CÁC HÀM CƠ BẢN (giữ nguyên ý tưởng bản gốc)
# ---------------------------------------------------------------------------

def get_parity(key, indices):
    """Parity (XOR) của các bit tại các vị trí `indices`."""
    return sum(key[i] for i in indices) % 2


def binary_search_error(alice_key, bob_key, indices):
    """Tìm kiếm nhị phân định vị CHÍNH XÁC 1 bit sai trong 1 khối đã biết là lỗi.
    Trả về index gốc (trong khóa ban đầu) của bit sai."""
    if len(indices) == 1:
        return indices[0]

    mid = len(indices) // 2
    left_half = indices[:mid]

    if get_parity(alice_key, left_half) != get_parity(bob_key, left_half):
        return binary_search_error(alice_key, bob_key, left_half)
    else:
        right_half = indices[mid:]
        return binary_search_error(alice_key, bob_key, right_half)


def generate_permutation(n, seed):
    """
    Sinh ra một THỨ TỰ chỉ số (không phải giá trị bit!) dùng để quyết định
    bit nào sẽ đứng cạnh bit nào khi cắt khối ở vòng này.

    Ví dụ n=8:
        seed=None -> indices = [0,1,2,3,4,5,6,7]           (giữ nguyên)
        seed=42   -> indices = [5,1,7,0,3,6,2,4] (ví dụ)    (đã xáo trộn)

    Mục đích: nếu 2 lỗi (ví dụ index 2 và 5) luôn đứng cạnh nhau ở MỌI vòng,
    chúng sẽ MÃI MÃI nằm chung 1 khối và có thể mãi mãi ẩn nhau (parity chẵn).
    Xáo trộn giúp 2 index này "chia tay" nhau ở vòng sau, rơi vào 2 khối
    khác nhau -> lỗi bị lộ ra riêng lẻ.
    """
    indices = list(range(n))
    # indices bây giờ là [0, 1, 2, ..., n-1] -- thứ tự gốc, CHƯA xáo trộn

    if seed is not None:
        # random.Random(seed) tạo 1 bộ sinh số ngẫu nhiên RIÊNG, không đụng
        # tới random toàn cục. Quan trọng: nếu Alice và Bob CÙNG dùng 1 seed
        # (ví dụ họ thống nhất seed=1001 cho vòng 2), .shuffle() sẽ luôn cho
        # ra ĐÚNG 1 kết quả xáo trộn giống hệt nhau ở cả 2 phía, dù họ chạy
        # độc lập trên máy khác nhau -- không cần gửi cả mảng qua kênh,
        # chỉ cần gửi con số seed (rất ngắn) là đủ để đồng bộ.
        random.Random(seed).shuffle(indices)
        # sau dòng này, indices bị xáo trộn TẠI CHỖ (in-place), ví dụ
        # từ [0,1,2,3,4,5,6,7] thành [5,1,7,0,3,6,2,4]

    # seed=None (dùng cho vòng 1) -> KHÔNG xáo trộn, trả về [0,1,...,n-1]
    # nguyên vẹn, đúng chuẩn Brassard-Salvail (vòng đầu tiên luôn giữ thứ tự
    # gốc để dễ đối chiếu / debug, các vòng sau mới bắt đầu xáo trộn).
    return indices


def build_blocks(permuted_indices, block_size):
    """
    Hàm này KHÔNG biết gì về xáo trộn cả -- nó chỉ làm đúng 1 việc là cắt
    một danh sách dài thành nhiều đoạn con liên tiếp, mỗi đoạn dài
    block_size phần tử. Input của nó CHÍNH LÀ output của generate_permutation
    ở trên, nên "liên tiếp trong permuted_indices" không có nghĩa là
    "liên tiếp trong khóa gốc".

    Ví dụ: permuted_indices = [5,1,7,0,3,6,2,4], block_size = 2
        -> các khối: [5,1] [7,0] [3,6] [2,4]
    Nhìn vào khối [5,1]: đây là khối gồm BIT TẠI VỊ TRÍ 5 và BIT TẠI VỊ TRÍ 1
    trong khóa gốc -- hai vị trí này vốn CÁCH XA NHAU trong khóa thật, chỉ
    vì permutation xếp chúng cạnh nhau ở vòng này mà thôi.
    """
    return [
        permuted_indices[i:i + block_size]   # cắt lát [i, i+block_size)
        for i in range(0, len(permuted_indices), block_size)
        # range nhảy từng bước block_size: 0, block_size, 2*block_size, ...
        # -> đảm bảo các khối không chồng lấn và phủ hết toàn bộ danh sách
    ]


# ---------------------------------------------------------------------------
# LỚP CASCADE - có backtracking đầy đủ
# ---------------------------------------------------------------------------

class Cascade:
    def __init__(self, alice_key, bob_key, qber_estimate, num_passes=4, verbose=True):
        self.alice = alice_key
        self.bob = bob_key
        self.n = len(alice_key)
        # QBER=0 sẽ làm chia cho 0, và QBER ước lượng từ mẫu nhỏ có thể vô tình
        # ra 0 dù thực tế còn lỗi (mẫu không trúng bit sai nào) -> luôn chặn dưới
        # QBER ở mức tối thiểu ~1 lỗi kỳ vọng trên toàn khóa, để block size đầu
        # không bị phóng đại quá mức.
        min_qber = 1.0 / max(len(alice_key), 1)
        self.qber = max(qber_estimate, min_qber, 1e-3)
        self.num_passes = num_passes
        self.verbose = verbose

        # Lưu cấu trúc từng vòng để backtracking có thể tra cứu lại
        # self.passes[p] = {'block_size':.., 'blocks': [[idx,...], ...]}
        self.passes = []

        # Đếm số bit thông tin đã "lộ" ra kênh công khai (mỗi lần so sánh
        # parity = lộ 1 bit) -> dùng cho Privacy Amplification sau này
        self.leaked_bits = 0
        self.total_corrections = 0

    # --- Chọn block size tối ưu theo QBER (công thức Brassard-Salvail) ---
    def compute_block_sizes(self):
        k1 = max(1, math.floor(0.73 / self.qber))
        # Chặn thực tế: nếu QBER ước lượng bị nhiễu (mẫu nhỏ, tình cờ = 0 hoặc
        # rất thấp), công thức lý thuyết có thể cho ra block gần bằng cả khóa,
        # khiến các lỗi có số lượng CHẴN trong 1 khối bị "ẩn" hoàn toàn (parity
        # trùng nhau). Giới hạn trần k1 <= n/4 là một biên an toàn thực dụng
        # thường dùng trong triển khai (không nằm trong công thức gốc, nhưng
        # cần thiết để thuật toán không "mù" khi ước lượng QBER kém chính xác).
        k1 = min(k1, max(2, self.n // 4))
        sizes = [k1]
        for _ in range(1, self.num_passes):
            sizes.append(sizes[-1] * 2)
        sizes = [min(s, self.n) for s in sizes]
        return sizes

    # --- So sánh parity 1 khối, có đếm số bit lộ ra kênh công khai ---
    def _parity_mismatch(self, block):
        self.leaked_bits += 1
        return get_parity(self.alice, block) != get_parity(self.bob, block)

    def _find_and_fix(self, block):
        """Nhị phân tìm + Bob tự sửa 1 bit sai trong block. Mỗi bước nhị phân
        cũng là 1 lần lộ parity công khai -> log2(len(block)) bit lộ thêm."""
        # đếm số bit lộ trong quá trình binary search (mỗi lần chia đôi = 1 so sánh)
        self.leaked_bits += max(0, math.ceil(math.log2(len(block)))) if len(block) > 1 else 0
        error_idx = binary_search_error(self.alice, self.bob, block)
        self.bob[error_idx] = 1 - self.bob[error_idx]
        self.total_corrections += 1
        return error_idx

    def _block_containing(self, pass_idx, global_idx):
        for block in self.passes[pass_idx]['blocks']:
            if global_idx in block:
                return block
        return None

    def _backtrack(self, fixed_idx, from_pass):
        """Sau khi sửa 1 bit ở vòng `from_pass`, quay lại kiểm tra các vòng
        TRƯỚC ĐÓ (from_pass-1, from_pass-2, ..., 0) xem khối nào chứa
        `fixed_idx` mà giờ bị lệch parity -> đó chính là hiệu ứng "cascade"."""
        for p in range(from_pass - 1, -1, -1):
            block = self._block_containing(p, fixed_idx)
            if block is None or len(block) <= 1:
                continue
            if self._parity_mismatch(block):
                new_idx = self._find_and_fix(block)
                if self.verbose:
                    print(f"      ↩️  [Backtrack -> Vòng {p + 1}] phát hiện & sửa "
                          f"thêm lỗi tại vị trí gốc {new_idx}")
                # đệ quy: bit vừa sửa lại có thể ảnh hưởng các vòng còn sớm hơn nữa
                self._backtrack(new_idx, p)

    def run(self):
        block_sizes = self.compute_block_sizes()
        if self.verbose:
            print(f"QBER ước lượng = {self.qber:.4f}")
            print(f"Block size các vòng (k1=floor(0.73/QBER), sau đó x2 mỗi vòng): {block_sizes}\n")

        for pass_idx, bsize in enumerate(block_sizes):
            # Đúng chuẩn: vòng 1 KHÔNG hoán vị, các vòng sau hoán vị ngẫu nhiên
            seed = None if pass_idx == 0 else 1000 + pass_idx
            perm = generate_permutation(self.n, seed)
            blocks = build_blocks(perm, bsize)
            self.passes.append({'block_size': bsize, 'blocks': blocks})

            if self.verbose:
                print(f"--- VÒNG {pass_idx + 1} (block_size={bsize}, seed={seed}) ---")

            fixed_this_pass = 0
            for block in blocks:
                if len(block) == 0:
                    continue
                if self._parity_mismatch(block):
                    error_idx = self._find_and_fix(block)
                    fixed_this_pass += 1
                    if self.verbose:
                        print(f"   🔧 Sửa lỗi tại vị trí gốc {error_idx}")
                    # BACKTRACKING: đây là phần bản demo ban đầu CÒN THIẾU
                    self._backtrack(error_idx, pass_idx)

            if self.verbose:
                print(f"   Hoàn thành vòng {pass_idx + 1}: sửa trực tiếp {fixed_this_pass} lỗi "
                      f"(chưa tính lỗi phát hiện thêm qua backtrack).\n")

            if self.alice == self.bob:
                if self.verbose:
                    print("   ✅ Khóa đã khớp hoàn toàn -> dừng sớm, không cần chạy thêm vòng.\n")
                return self.total_corrections

        # Nếu hết số vòng cố định mà vẫn còn lỗi số chẵn ẩn trong khối lớn,
        # đây là hạn chế đã biết của Cascade (không phải lỗi triển khai).
        # Cách xử lý chuẩn: chạy thêm các vòng "dọn dẹp" với block_size nhỏ
        # dần hoặc dùng thuật toán bổ sung BICONF (so sánh trực tiếp các tập
        # con ngẫu nhiên toàn khóa) cho tới khi khớp hoặc hết ngân sách vòng.
        extra_pass = self.num_passes
        max_extra_passes = 6
        while self.alice != self.bob and extra_pass < self.num_passes + max_extra_passes:
            bsize = max(2, self.n // (2 ** (extra_pass - self.num_passes + 2)))
            seed = 5000 + extra_pass
            perm = generate_permutation(self.n, seed)
            blocks = build_blocks(perm, bsize)
            self.passes.append({'block_size': bsize, 'blocks': blocks})
            if self.verbose:
                print(f"--- VÒNG DỌN DẸP {extra_pass + 1} (block_size={bsize}, seed={seed}) ---")
            for block in blocks:
                if len(block) == 0:
                    continue
                if self._parity_mismatch(block):
                    error_idx = self._find_and_fix(block)
                    if self.verbose:
                        print(f"   🔧 Sửa lỗi tại vị trí gốc {error_idx}")
                    self._backtrack(error_idx, extra_pass)
            extra_pass += 1
            if self.verbose:
                print()

        return self.total_corrections


# ---------------------------------------------------------------------------
# MÔ PHỎNG TOÀN BỘ FLOW QKD: sifting -> ước lượng QBER -> ngưỡng an toàn ->
# Cascade -> Privacy Amplification
# ---------------------------------------------------------------------------

def simulate_qkd_flow():
    rng = random.Random(7)
    n = 20000

    # --- Giả lập kết quả SAU BƯỚC SIFTING (đã lọc theo basis trùng nhau) ---
    alice_sifted = [rng.randint(0, 1) for _ in range(n)]
    bob_sifted = alice_sifted.copy()

    # Giả lập nhiễu kênh lượng tử: cài lỗi thật theo 1 QBER "thật" (Bob không biết)
    true_qber = 0.03
    num_real_errors = int(n * true_qber)
    error_positions = rng.sample(range(n), num_real_errors)
    for idx in error_positions:
        bob_sifted[idx] = 1 - bob_sifted[idx]

    print(f"[Sifted key] độ dài {n} bit, số lỗi thật đã cài: {num_real_errors} "
          f"tại vị trí {sorted(error_positions)}\n")

    # --- BƯỚC 1: ước lượng QBER bằng cách công khai 1 phần mẫu ngẫu nhiên ---
    # (các bit đã công khai so sánh thì phải LOẠI BỎ khỏi khóa, vì Eve cũng nghe được)
    sample_size = int(n * 0.1)
    sample_positions = rng.sample(range(n), sample_size)
    sample_errors = sum(1 for i in sample_positions if alice_sifted[i] != bob_sifted[i])
    qber_estimate = sample_errors / sample_size
    print(f"[Ước lượng QBER] lấy mẫu công khai {sample_size} bit -> "
          f"QBER ước lượng thô (điểm) = {qber_estimate:.4f}")

    # An toàn hơn: không dùng thẳng qber_estimate (dễ bị lệch do may rủi lấy
    # mẫu), mà dùng CẬN TRÊN thống kê với xác suất thất bại epsilon cực nhỏ.
    # epsilon càng nhỏ -> cận trên càng "rộng tay", càng an toàn (khó bị Eve
    # qua mặt) nhưng cũng dễ hủy oan phiên khóa tốt hơn -> đây là tham số
    # bảo mật (security parameter) phải chọn trước, không tùy tiện đổi.
    epsilon = 1e-6
    qber_bound = serfling_upper_bound(qber_estimate, n, sample_size, epsilon)
    print(f"[Serfling bound] với xác suất thất bại epsilon={epsilon:.0e} -> "
          f"QBER cận trên (dùng để quyết định) = {qber_bound:.4f}")

    remain = [i for i in range(n) if i not in sample_positions]
    alice_key = [alice_sifted[i] for i in remain]
    bob_key = [bob_sifted[i] for i in remain]
    print(f"[Sau loại mẫu] khóa làm việc còn {len(alice_key)} bit\n")

    # --- BƯỚC 2: kiểm tra ngưỡng an toàn (BB84 lý thuyết ~11%) ---
    # So sánh CẬN TRÊN (không phải điểm ước lượng thô) với ngưỡng, để quyết
    # định có đủ an toàn tin tưởng không, đúng tinh thần security proof thật.
    QBER_THRESHOLD = 0.11
    if qber_bound > QBER_THRESHOLD:
        print(f"❌ QBER cận trên ({qber_bound:.4f}) vượt ngưỡng ({QBER_THRESHOLD}) "
              f"-> NGHI CÓ NGHE LÉN (hoặc mẫu không đủ để tin tưởng), HỦY PHIÊN KHÓA!")
        return

    print(f"✅ QBER cận trên vẫn dưới ngưỡng {QBER_THRESHOLD} -> tiến hành đối soát lỗi (Cascade)\n")

    real_errors_remaining = sum(1 for a, b in zip(alice_key, bob_key) if a != b)
    print(f"[Trước Cascade] số lỗi thật còn lại trong khóa làm việc: {real_errors_remaining}\n")

    # --- BƯỚC 3: CASCADE RECONCILIATION ---
    cascade = Cascade(alice_key, bob_key, qber_bound, num_passes=4)
    total_corrections = cascade.run()

    match = alice_key == bob_key
    print("--- KẾT QUẢ CASCADE ---")
    print(f"Tổng số lần sửa bit (kể cả do backtrack phát hiện thêm): {total_corrections}")
    print(f"Số bit đã lộ ra kênh công khai qua các lần so sánh parity: {cascade.leaked_bits}")
    print(f"Khóa Alice == Khóa Bob sau Cascade: {match}\n")

    if not match:
        print("⚠️ Vẫn còn lỗi sau các vòng đã chạy -> cần thêm vòng hoặc dùng BICONF để dọn nốt.")
        return

    # --- BƯỚC 4: PRIVACY AMPLIFICATION (rút gọn khóa) ---
    # Nguyên tắc: độ dài khóa cuối phải trừ đi toàn bộ thông tin đã lộ công khai
    # (bit mẫu QBER + bit parity trong Cascade), cộng biên an toàn.
    leaked_total = sample_size + cascade.leaked_bits
    security_margin = 20  # biên an toàn thêm (tham số thực tế phụ thuộc mô hình bảo mật)
    final_len = max(0, len(alice_key) - leaked_total - security_margin)

    print(f"[Privacy Amplification] tổng bit đã lộ: {leaked_total} "
          f"(mẫu QBER: {sample_size} + parity Cascade: {cascade.leaked_bits})")
    print(f"-> Băm (hash) khóa {len(alice_key)} bit xuống còn ~{final_len} bit "
          f"làm FINAL KEY dùng chung, an toàn trước Eve.")

def simulate_bob_alice_flow(alice_sifted, bob_sifted):
    n = len(alice_sifted)
    # Giả lập nhiễu kênh lượng tử: cài lỗi thật theo 1 QBER "thật" (Bob không biết)
    true_qber = 0.03
    num_real_errors = int(n * true_qber)
    error_positions = rng.sample(range(n), num_real_errors)
    for idx in error_positions:
        bob_sifted[idx] = 1 - bob_sifted[idx]

    print(f"[Sifted key] độ dài {n} bit, số lỗi thật đã cài: {num_real_errors} "
          f"tại vị trí {sorted(error_positions)}\n")

    # --- BƯỚC 1: ước lượng QBER bằng cách công khai 1 phần mẫu ngẫu nhiên ---
    # (các bit đã công khai so sánh thì phải LOẠI BỎ khỏi khóa, vì Eve cũng nghe được)
    sample_size = int(n * 0.1)
    sample_positions = rng.sample(range(n), sample_size)
    sample_errors = sum(1 for i in sample_positions if alice_sifted[i] != bob_sifted[i])
    qber_estimate = sample_errors / sample_size
    print(f"[Ước lượng QBER] lấy mẫu công khai {sample_size} bit -> "
          f"QBER ước lượng thô (điểm) = {qber_estimate:.4f}")

    # An toàn hơn: không dùng thẳng qber_estimate (dễ bị lệch do may rủi lấy
    # mẫu), mà dùng CẬN TRÊN thống kê với xác suất thất bại epsilon cực nhỏ.
    # epsilon càng nhỏ -> cận trên càng "rộng tay", càng an toàn (khó bị Eve
    # qua mặt) nhưng cũng dễ hủy oan phiên khóa tốt hơn -> đây là tham số
    # bảo mật (security parameter) phải chọn trước, không tùy tiện đổi.
    epsilon = 1e-6
    qber_bound = serfling_upper_bound(qber_estimate, n, sample_size, epsilon)
    print(f"[Serfling bound] với xác suất thất bại epsilon={epsilon:.0e} -> "
          f"QBER cận trên (dùng để quyết định) = {qber_bound:.4f}")

    remain = [i for i in range(n) if i not in sample_positions]
    alice_key = [alice_sifted[i] for i in remain]
    bob_key = [bob_sifted[i] for i in remain]
    print(f"[Sau loại mẫu] khóa làm việc còn {len(alice_key)} bit\n")

    # --- BƯỚC 2: kiểm tra ngưỡng an toàn (BB84 lý thuyết ~11%) ---
    # So sánh CẬN TRÊN (không phải điểm ước lượng thô) với ngưỡng, để quyết
    # định có đủ an toàn tin tưởng không, đúng tinh thần security proof thật.
    QBER_THRESHOLD = 0.11
    if qber_bound > QBER_THRESHOLD:
        print(f"❌ QBER cận trên ({qber_bound:.4f}) vượt ngưỡng ({QBER_THRESHOLD}) "
              f"-> NGHI CÓ NGHE LÉN (hoặc mẫu không đủ để tin tưởng), HỦY PHIÊN KHÓA!")
        return

    print(f"✅ QBER cận trên vẫn dưới ngưỡng {QBER_THRESHOLD} -> tiến hành đối soát lỗi (Cascade)\n")

    real_errors_remaining = sum(1 for a, b in zip(alice_key, bob_key) if a != b)
    print(f"[Trước Cascade] số lỗi thật còn lại trong khóa làm việc: {real_errors_remaining}\n")

    # --- BƯỚC 3: CASCADE RECONCILIATION ---
    cascade = Cascade(alice_key, bob_key, qber_bound, num_passes=4)
    total_corrections = cascade.run()

    match = alice_key == bob_key
    print("--- KẾT QUẢ CASCADE ---")
    print(f"Tổng số lần sửa bit (kể cả do backtrack phát hiện thêm): {total_corrections}")
    print(f"Số bit đã lộ ra kênh công khai qua các lần so sánh parity: {cascade.leaked_bits}")
    print(f"Khóa Alice == Khóa Bob sau Cascade: {match}\n")

    if not match:
        print("⚠️ Vẫn còn lỗi sau các vòng đã chạy -> cần thêm vòng hoặc dùng BICONF để dọn nốt.")
        return {"success": false, "message": 'Bob key and alice key still have mismatch after error simulation'}

    # --- BƯỚC 4: PRIVACY AMPLIFICATION (rút gọn khóa) ---
    # Nguyên tắc: độ dài khóa cuối phải trừ đi toàn bộ thông tin đã lộ công khai
    # (bit mẫu QBER + bit parity trong Cascade), cộng biên an toàn.
    leaked_total = sample_size + cascade.leaked_bits
    security_margin = 20  # biên an toàn thêm (tham số thực tế phụ thuộc mô hình bảo mật)
    final_len = max(0, len(alice_key) - leaked_total - security_margin)

    print(f"[Privacy Amplification] tổng bit đã lộ: {leaked_total} "
          f"(mẫu QBER: {sample_size} + parity Cascade: {cascade.leaked_bits})")
    print(f"-> Băm (hash) khóa {len(alice_key)} bit xuống còn ~{final_len} bit "
          f"làm FINAL KEY dùng chung, an toàn trước Eve.")
