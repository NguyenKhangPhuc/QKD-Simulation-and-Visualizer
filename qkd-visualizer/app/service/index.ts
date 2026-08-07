import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json',
  },
});

export * from './initialize_connection';
