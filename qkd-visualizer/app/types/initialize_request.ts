export interface InitializeConnectionRequest {
  num_bits: number;
  is_eve: boolean;
  distance_km?: number;
  depolarization_rate?: number;
  eve_intercept_prob?: number;
  detector_efficiency?: number;
  epsilon?: number;
}

export interface InitializeConnectionResponse {
  status: "success" | "aborted";
  reason?: string;
  initial_alice_bits: number[];
  initial_alice_bases: number[];
  eve_bases?: number[];
  eve_measured_bits?: number[];
  initial_bob_bases: Record<number, number>;
  initial_bob_bits: Record<number, number>;
  matching_indices_alice_bob: number[];
  sample_size_qber: number;
  sample_indices_qber: number[];
  sample_bits_qber: number[];
  mismatches?: number;
  qber: number;
  qber_bound?: number;
  received_photon_count?: number;
  // Key progression
  alice_raw_key?: string;
  alice_reconciled_key?: string;
  alice_secret_final_key?: string;
  bob_raw_key?: string;
  bob_reconciled_key?: string;
  bob_secret_final_key?: string;
  // Cascade stats
  leaked_bits?: number;
  corrections?: number;
  is_final_key_matched?: boolean;
  // Legacy / convenience
  alice_final_key?: string;
  bob_final_key?: string;
  encrypted_message?: string;
}
