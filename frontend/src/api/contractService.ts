import { request } from './client';
import { ContractItem } from '../types';

export const contractService = {
  getContracts: (): Promise<ContractItem[]> => {
    return request<ContractItem[]>('/api/contracts');
  },
};
