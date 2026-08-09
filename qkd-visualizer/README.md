# QKD Protocol Simulator and Visualizer

A Next.js frontend application designed to visualize the BB84 Quantum Key Distribution (QKD) protocol. This application communicates with Alice (Python client) and Bob (Python server) backend services to run quantum state simulations and present the step-by-step sifting, QBER checking, and final key generation.

## Project Description

The qkd-visualizer is a Next.js application built with TypeScript, Tailwind CSS, and Framer Motion. It acts as the interactive dashboard for the BB84 simulation. It allows users to set simulation parameters, trigger quantum key generation, and navigate through the different phases of the protocol (state preparation, eavesdropping, measurement, basis sifting, QBER checking, and symmetric key encryption).

## Features and Capabilities

*   Interactive BB84 Simulation Settings: Configure the number of qubits (50 to 1000) and toggle the presence of an eavesdropper (Eve).
*   Step-by-Step Protocol Walkthrough: Navigate through 6 distinct stages of the protocol:
    1.  Alice's State Preparation: Visualization of raw bits, encoding bases, and the resulting qubit states.
    2.  Eve's Interception: Visualization of eavesdropping measurement bases, measured bits, and collapsed re-encoded states (if Eve is enabled).
    3.  Bob's Measurement: Bob's random bases and final measured bits.
    4.  Classical Basis Sifting: Comparison of Alice and Bob's bases to keep matching entries.
    5.  QBER Verification: Display of a 20% sample and error rate (QBER) calculation to detect eavesdropping.
    6.  Final Shared Secret: Display of the derived AES symmetric key and confirmation of encryption/decryption.
*   Dynamic Column Visibility Controls: Adjust how many qubits (up to 12) are displayed simultaneously with smart horizontal pagination and vertical dot indicators.
*   Grayscale Monochrome Design System: A clean black-and-white theme featuring high-contrast text and custom shadows for clear visual boundaries.

## Tech Stack and Prerequisites

*   Framework: Next.js 15 (Turbopack)
*   Language: TypeScript
*   Styling: Tailwind CSS 4, Framer Motion for smooth slide transitions
*   HTTP Client: Axios for API communication
*   Backend Requirements: Python 3 backend running Alice (alice_client.py) and Bob (bob_server.py)

## Directory Structure

The structure of the app directory is as follows:

```
qkd-visualizer/app/
├── components/
│   ├── HeroSection.tsx          # Hero page with scrolling CTA button
│   ├── QkdVisualizerSection.tsx  # Settings form and step-by-step orchestrator
│   ├── QuantumTable.tsx         # Reusable tabular viewer with ellipsis pagination
│   ├── StepAliceTable.tsx       # Table showing Alice's qubit encoding
│   ├── StepBobTable.tsx         # Table showing Bob's basis choices and measurement
│   ├── StepEveTable.tsx         # Table showing Eve's interception details
│   ├── StepFinalKey.tsx         # Layout showing the derived keys and status
│   ├── StepNavigator.tsx        # Top indicator bar and column pagination controls
│   ├── StepQBERTable.tsx        # Table showing error calculations and threshold progress bar
│   └── StepSiftingTable.tsx     # Double table layout comparing bases and raw key bits
├── constants/
│   └── design-tokens.ts         # Grayscale color palette, gradients, and shadow tokens
├── service/
│   ├── index.ts                 # Axios API client pointing to http://localhost:8001
│   └── initialize_connection.ts # API caller for backend initialization
├── types/
│   └── initialize_request.ts    # TypeScript interface definitions for request/response payloads
├── globals.css                  # Custom scrollbar styles and Tailwind imports
├── layout.tsx                   # HTML document root wrapper
└── page.tsx                     # Main layout mounting the Hero and Visualizer components
```

## How the Application Works

1.  **User Configuration**: The user inputs the number of qubits and toggles Eve on or off in the Visualizer Section.
2.  **API Call**: On submission, the application calls the initialize_connection endpoint on the Alice client (http://localhost:8001).
3.  **Backend Protocol Execution**:
    *   Alice client generates random bits and bases, and encodes them into QASM representations.
    *   If Eve is enabled, Alice's client measures and re-encodes the qubits.
    *   Qubits are posted to Bob's server (http://localhost:8000) for measurement.
    *   Classical sifting and QBER checks are executed via HTTP requests between Alice and Bob.
    *   Alice encrypts a message using the derived key and sends it to Bob, who decrypts it.
4.  **UI Visualization**: The API returns the entire protocol trace. The Next.js frontend uses state management to let the user step through each phase, displaying the exact states, bases, and outcomes.

## Installation and Setup Instructions

1.  Install dependencies:
    ```bash
    npm install
    ```
2.  Run the development server:
    ```bash
    npm run dev
    ```
3.  Ensure the Python backend (Alice client on port 8001 and Bob server on port 8000) is running to allow successful API connections.
