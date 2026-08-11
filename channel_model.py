"""
channel_model.py
Simulates a physical optical fiber channel with attenuation, depolarization, and Eve interception.
"""
import random
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
import qiskit.qasm2 as qasm2

SIMULATOR = AerSimulator()


class RealisticQuantumChannel:
    def __init__(
        self,
        distance_km: float = 10.0,
        attenuation_db_per_km: float = 0.2,  # Standard 1550nm fiber loss
        depolarization_rate: float = 0.02,  # Channel depolarization noise
        detector_efficiency: float = 0.85,  # Bob's SPAD detector efficiency
        dark_count_prob: float = 1e-4,  # Random thermal dark count
        is_eve: bool = False,
        eve_intercept_prob: float = 1.0,  # Fraction of qubits Eve intercepts
    ):
        self.distance_km = distance_km
        self.depolarization_rate = depolarization_rate
        self.detector_efficiency = detector_efficiency
        self.dark_count_prob = dark_count_prob
        self.is_eve = is_eve
        self.eve_intercept_prob = eve_intercept_prob

        # Transmittance formula: T = 10^(-alpha * d / 10)
        self.transmittance = 10 ** (-(attenuation_db_per_km * distance_km) / 10.0)
        self.noise_model = self._build_noise_model()

    def _build_noise_model(self) -> NoiseModel:
        noise = NoiseModel()
        if self.depolarization_rate > 0:
            error = depolarizing_error(self.depolarization_rate, 1)
            noise.add_all_qubit_quantum_error(error, ["h", "x", "id", "measure"])
        return noise

    def transmit(self, qasm_strings: list[str]):
        """
        Processes QASM qubits through Eve, fiber attenuation, and channel noise.

        Returns:
            processed_qasm (list[str]): QASM strings of photons that reached Bob.
            received_indices (list[int]): Indices of photons that survived transmission.
            eve_info (dict): Diagnostic info about Eve's eavesdropping.
        """
        received_qasm = []
        received_indices = []
        eve_bases = []
        eve_measured_bits = []

        for idx, qasm_str in enumerate(qasm_strings):
            qc = qasm2.loads(qasm_str)

            # 1. Eve Interception (Selective / Partial Attack)
            if self.is_eve and random.random() < self.eve_intercept_prob:
                eve_basis = random.randint(0, 1)
                eve_bases.append(eve_basis)

                intercept_qc = qc.copy()
                if eve_basis == 1:
                    intercept_qc.h(0)
                intercept_qc.measure(0, 0)

                res = SIMULATOR.run(intercept_qc, shots=1).result().get_counts()
                measured_bit = int(list(res.keys())[0])
                eve_measured_bits.append(measured_bit)

                # Re-encode state for Bob
                qc = QuantumCircuit(1, 1)
                if measured_bit == 1:
                    qc.x(0)
                if eve_basis == 1:
                    qc.h(0)

            # 2. Fiber Attenuation & Detection Survival Probability
            survival_prob = self.transmittance * self.detector_efficiency
            if random.random() <= survival_prob:
                # Photon survived transmission and was detected
                received_qasm.append(qasm2.dumps(qc))
                received_indices.append(idx)
            elif random.random() < self.dark_count_prob:
                # Detector Dark Count: random fake photon triggered at detector
                fake_qc = QuantumCircuit(1, 1)
                if random.random() > 0.5:
                    fake_qc.x(0)
                received_qasm.append(qasm2.dumps(fake_qc))
                received_indices.append(idx)
            # Else: Photon lost permanently in transit (sifting handles index mismatch)

        eve_info = {"eve_bases": eve_bases, "eve_measured_bits": eve_measured_bits}

        return received_qasm, received_indices, eve_info, self.noise_model
