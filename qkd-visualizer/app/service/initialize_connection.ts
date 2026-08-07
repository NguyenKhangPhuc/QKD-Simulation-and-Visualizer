import { apiClient } from './index';
import { InitializeConnectionRequest, InitializeConnectionResponse } from '../types/initialize_request';

export const initializeConnection = async (
  payload: InitializeConnectionRequest
): Promise<InitializeConnectionResponse> => {
  const response = await apiClient.post<InitializeConnectionResponse>('/initialize_connection', payload);
  return response.data;
};
