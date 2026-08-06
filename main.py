from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
q = QuantumRegister(3, 'q')
c = ClassicalRegister(1, 'c')
qc = QuantumCircuit(q, c)

qc.x(q[0])
qc.x(q[1])

def reversible_xor(qc, a,b,target):
    qc.cx(a,target)
    qc.cx(b,target)

def reversible_and(qc,a,b,target):
    qc.ccx(a,b,target)

def reversible_or(qc,a,b,target):
    qc.cx(a,target)
    qc.cx(b,target)
    qc.ccx(a,b,target)
    
qc.ccx(q[0],q[1],q[2])

qc.measure(q[2], c[0])

simulator = AerSimulator()
job = simulator.run(qc, shots=1000) # Chạy mô phỏng 1000 lần
result = job.result()
counts = result.get_counts()

print("Kết quả đo (Counts):", counts)

print(qc.draw('text'))