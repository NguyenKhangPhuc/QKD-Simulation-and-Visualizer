export interface InitializeConnectionRequest {
  num_bits: number;
  is_eve: boolean;
  distance_km?: number;
  depolarization_rate?: number;
  eve_intercept_prob?: number;
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
  received_photon_count?: number;
  alice_final_key?: string;
  bob_final_key?: string;
  encrypted_message?: string;
}
