"""
Cascade Protocol - Implementation following Brassard & Salvail (1994)
================================================================================
Key improvements over the basic demo:
  1. Round 1 block size chosen via optimal formula: k1 = floor(0.73 / QBER)
     Subsequent rounds: k_i = 2 * k_(i-1) (doubles each round).
  2. BACKTRACKING: whenever a bit is corrected in the current round, all blocks
     from all previous rounds containing that position are re-checked, because
     flipping a bit can expose a previously hidden second error (the cascade
     effect).
  3. Fully distributed: Alice's key is never accessed directly. Two callbacks
     are injected into Cascade:
       - alice_parity_fn(block: list[int]) -> int
           Returns Alice's XOR parity (0 or 1) for the given block of indices.
           Implemented as HTTP POST to Alice's server.
       - confirm_key_fn(bob_key: list[int]) -> bool
           Returns True if Alice's raw key matches Bob's current reconciled key,
           compared via SHA-256 hash. Implemented as HTTP POST to Alice's server.
"""

import math
import random
import numpy as np


def toeplitz_hash(key_str: str, final_len: int, seed: int) -> str:
    """
    Compress a bit-string key of length N down to final_len (M) bits using a
    random Toeplitz matrix over GF(2).

    A Toeplitz matrix T is fully defined by a single vector of length (N + M - 1)
    via the element formula:
        # T[i, j] = toeplitz_vector[N - 1 + j - i]

    Both Alice and Bob use the same seed to independently reproduce the same
    matrix without exchanging it over the channel.

    Args:
        key_str: Binary string of 0s and 1s (length N).
        final_len: Desired output length M (must satisfy 0 < M <= N).
        seed: Random seed shared between Alice and Bob.

    Returns:
        Binary string of length final_len.
    """
    key_bits = np.array([int(bit) for bit in key_str], dtype=int)
    n = len(key_bits)

    if final_len <= 0 or final_len > n:
        raise ValueError("final_len must satisfy 0 < final_len <= len(key_str).")

    # Generate the defining vector for the Toeplitz matrix
    rng = np.random.default_rng(seed)
    toeplitz_vector = rng.integers(0, 2, size=(n + final_len - 1))

    # Build index lookup: T[i, j] = toeplitz_vector[final_len - 1 + j - i]
    # Valid index range: [0, n + final_len - 2], which matches the vector size exactly.
    i_indices = np.arange(final_len)[:, None]
    j_indices = np.arange(n)
    matrix_indices = final_len - 1 + j_indices - i_indices
    toeplitz_matrix = toeplitz_vector[matrix_indices]

    # GF(2) matrix-vector product: dot product modulo 2
    hashed_bits = np.dot(toeplitz_matrix, key_bits) % 2

    return "".join(map(str, hashed_bits))


# ---------------------------------------------------------------------------
# QBER UPPER BOUND: Serfling inequality (sampling without replacement)
# ---------------------------------------------------------------------------

def serfling_upper_bound(sample_qber: float, n: int, m: int, epsilon: float) -> float:
    """
    Compute a statistical upper bound on the true QBER (over the unseen key
    portion) at confidence level (1 - epsilon), using Serfling's inequality.

    For a finite population of size n and a sample of size m:
        delta = sqrt( ln(1/epsilon) * (1 - (m-1)/n) / (2*m) )
    Upper bound = sample_qber + delta, capped at 1.0.

    Using this bound instead of the raw sample QBER ensures that a lucky
    low-noise sample does not falsely certify a compromised channel as secure.

    Args:
        sample_qber: Observed error rate in the public QBER sample.
        n: Total sifted bits (size of the matching indices pool).
        m: Sample size used for QBER estimation.
        epsilon: Acceptable failure probability (security parameter).

    Returns:
        Statistical upper bound on the true QBER.
    """
    m = max(1, m)
    finite_population_factor = max(0.0, 1 - (m - 1) / n)
    delta = math.sqrt(math.log(1 / epsilon) * finite_population_factor / (2 * m))
    return min(1.0, sample_qber + delta)


# ---------------------------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------------------------

def get_parity(key: list, indices: list) -> int:
    """XOR parity of bits at the given indices in key."""
    return sum(key[i] for i in indices) % 2


def generate_permutation(n: int, seed) -> list:
    """
    Generate a permutation of [0, n-1] for a given Cascade round.

    Round 1 uses seed=None (identity permutation, preserving original order per
    the Brassard-Salvail specification). Later rounds use a deterministic seed so
    that both Alice and Bob independently reproduce the same permutation without
    transmitting the full array — only the short integer seed needs to be agreed upon.

    Args:
        n: Key length.
        seed: Integer seed, or None for the identity permutation.

    Returns:
        A list of n indices (permuted or in original order).
    """
    indices = list(range(n))
    if seed is not None:
        random.Random(seed).shuffle(indices)
    return indices


def build_blocks(permuted_indices: list, block_size: int) -> list:
    """
    Partition a permuted index list into consecutive non-overlapping blocks.

    Args:
        permuted_indices: Output of generate_permutation.
        block_size: Maximum number of indices per block.

    Returns:
        List of blocks, where each block is a list of global key indices.
    """
    return [
        permuted_indices[i:i + block_size]
        for i in range(0, len(permuted_indices), block_size)
    ]


# ---------------------------------------------------------------------------
# CASCADE CLASS — full backtracking, distributed (no direct Alice key access)
# ---------------------------------------------------------------------------

class Cascade:
    def __init__(
        self,
        bob_key: list,
        qber_estimate: float,
        alice_parity_fn,
        confirm_key_fn,
        num_passes: int = 4,
        verbose: bool = True,
    ):
        """
        Initialize the Cascade error reconciliation protocol.

        Args:
            bob_key: Bob's sifted raw key as a mutable list of ints (0 or 1).
                     This list is corrected IN PLACE during reconciliation.
            qber_estimate: Serfling upper bound on the true QBER.
            alice_parity_fn: Callable(block: list[int]) -> int.
                             Returns Alice's XOR parity for the given block
                             of key indices. Each call leaks exactly 1 bit and
                             is implemented as an HTTP POST to Alice's server.
            confirm_key_fn: Callable(bob_key: list[int]) -> bool.
                            Returns True if Bob's current key matches Alice's key
                            (compared via SHA-256). Used for early termination.
            num_passes: Number of main Cascade rounds (default: 4).
            verbose: Print debug output if True.
        """
        self.bob = bob_key
        self.n = len(bob_key)
        self.alice_parity_fn = alice_parity_fn
        self.confirm_key_fn = confirm_key_fn

        # Clamp QBER to avoid division-by-zero and excessively large block sizes
        min_qber = 1.0 / max(self.n, 1)
        self.qber = max(qber_estimate, min_qber, 1e-3)
        self.num_passes = num_passes
        self.verbose = verbose

        # Round history used by backtracking to locate prior-round blocks
        self.passes = []

        # Statistics: bits leaked to the public channel (for privacy amplification)
        self.leaked_bits = 0
        self.total_corrections = 0

    def compute_block_sizes(self) -> list:
        """
        Compute optimal block sizes for each round using the Brassard-Salvail
        formula: k1 = floor(0.73 / QBER), capped at n/4 to avoid hiding even
        numbers of errors inside a single oversized block. Subsequent rounds
        double the block size.
        """
        k1 = max(1, math.floor(0.73 / self.qber))
        k1 = min(k1, max(2, self.n // 4))
        sizes = [k1]
        for _ in range(1, self.num_passes):
            sizes.append(sizes[-1] * 2)
        return [min(s, self.n) for s in sizes]

    def _parity_mismatch(self, block: list) -> bool:
        """
        Ask Alice for her parity on this block and compare with Bob's.
        Each call to this method leaks exactly 1 bit to the public channel.
        """
        self.leaked_bits += 1
        alice_p = self.alice_parity_fn(block)
        bob_p = get_parity(self.bob, block)
        return alice_p != bob_p

    def _binary_search_error(self, block: list) -> int:
        """
        Recursively bisect block to locate the single erroneous bit position.
        Each recursive step makes one alice_parity_fn call (leaks 1 bit).

        Args:
            block: List of global key indices, guaranteed to contain exactly
                   one disagreeing bit between Alice and Bob.

        Returns:
            Global index (into the flat key) of the erroneous bit.
        """
        if len(block) == 1:
            return block[0]

        mid = len(block) // 2
        left_half = block[:mid]

        self.leaked_bits += 1
        alice_p = self.alice_parity_fn(left_half)
        bob_p = get_parity(self.bob, left_half)

        if alice_p != bob_p:
            return self._binary_search_error(left_half)
        else:
            return self._binary_search_error(block[mid:])

    def _find_and_fix(self, block: list) -> int:
        """
        Locate the erroneous bit in block via binary search and flip it in
        Bob's key. Increments total_corrections by 1.

        Returns:
            Global index of the corrected bit.
        """
        error_idx = self._binary_search_error(block)
        self.bob[error_idx] = 1 - self.bob[error_idx]
        self.total_corrections += 1
        return error_idx

    def _block_containing(self, pass_idx: int, global_idx: int):
        """Return the block in pass_idx's round that contains global_idx, or None."""
        for block in self.passes[pass_idx]['blocks']:
            if global_idx in block:
                return block
        return None

    def _backtrack(self, fixed_idx: int, from_pass: int):
        """
        After correcting a bit at from_pass, revisit all earlier rounds to
        check whether any block containing fixed_idx now has a parity mismatch.
        This is the core cascade effect: one correction can unmask further errors
        that were previously hidden (two errors in the same block cancel out).
        Recurses if another error is discovered and fixed.
        """
        for p in range(from_pass - 1, -1, -1):
            block = self._block_containing(p, fixed_idx)
            if block is None or len(block) <= 1:
                continue
            if self._parity_mismatch(block):
                new_idx = self._find_and_fix(block)
                if self.verbose:
                    print(f"      [Backtrack -> Round {p + 1}] detected & fixed error at index {new_idx}")
                self._backtrack(new_idx, p)

    def run(self) -> int:
        """
        Execute the Cascade reconciliation protocol.

        Runs num_passes main rounds (each with doubled block size), followed by
        up to 6 cleanup rounds if residual even-count errors remain.

        Returns:
            Total number of bit corrections performed.
        """
        block_sizes = self.compute_block_sizes()
        if self.verbose:
            print(f"QBER estimate = {self.qber:.4f}")
            print(f"Block sizes (k1=floor(0.73/QBER), doubling each round): {block_sizes}\n")

        for pass_idx, bsize in enumerate(block_sizes):
            seed = None if pass_idx == 0 else 1000 + pass_idx
            perm = generate_permutation(self.n, seed)
            blocks = build_blocks(perm, bsize)
            self.passes.append({'block_size': bsize, 'blocks': blocks})

            if self.verbose:
                print(f"--- ROUND {pass_idx + 1} (block_size={bsize}, seed={seed}) ---")

            fixed_this_pass = 0
            for block in blocks:
                if not block:
                    continue
                if self._parity_mismatch(block):
                    error_idx = self._find_and_fix(block)
                    fixed_this_pass += 1
                    if self.verbose:
                        print(f"   [Fix] corrected error at index {error_idx}")
                    self._backtrack(error_idx, pass_idx)

            if self.verbose:
                print(f"   Round {pass_idx + 1} complete: {fixed_this_pass} direct corrections.\n")

            if self.confirm_key_fn(self.bob):
                if self.verbose:
                    print("   Keys fully match — stopping early.\n")
                return self.total_corrections

        # Cleanup passes for residual even-count errors (known Cascade limitation)
        extra_pass = self.num_passes
        max_extra_passes = 6
        while not self.confirm_key_fn(self.bob) and extra_pass < self.num_passes + max_extra_passes:
            bsize = max(2, self.n // (2 ** (extra_pass - self.num_passes + 2)))
            seed = 5000 + extra_pass
            perm = generate_permutation(self.n, seed)
            blocks = build_blocks(perm, bsize)
            self.passes.append({'block_size': bsize, 'blocks': blocks})
            if self.verbose:
                print(f"--- CLEANUP ROUND {extra_pass + 1} (block_size={bsize}, seed={seed}) ---")
            for block in blocks:
                if not block:
                    continue
                if self._parity_mismatch(block):
                    error_idx = self._find_and_fix(block)
                    if self.verbose:
                        print(f"   [Fix] corrected error at index {error_idx}")
                    self._backtrack(error_idx, extra_pass)
            extra_pass += 1
            if self.verbose:
                print()

        return self.total_corrections
