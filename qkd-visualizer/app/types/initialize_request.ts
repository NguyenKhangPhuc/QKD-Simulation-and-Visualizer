export interface InitializeConnectionRequest {
  num_bits: number;
  is_eve: boolean;
}

export interface InitializeConnectionResponse {
  initial_alice_bits: number[];
  initial_alice_bases: number[];
  eve_bases?: number[];
  eve_measured_bits?: number[];
  initial_bob_bases: number[];
  initial_bob_bits: number[];
  matching_indices_alice_bob: number[];
  sample_size_qber: number;
  sample_indices_qber: number[];
  sample_bits_qber: number[];
  mismatches?: number;
  qber: number;
  alice_final_key?: string;
  bob_final_key?: string;
}
