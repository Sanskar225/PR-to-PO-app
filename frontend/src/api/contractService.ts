import { request } from './client';
import { ContractItem } from '../types';

export const contractService = {
  getContracts: (): Promise<ContractItem[]> => {
    return request<ContractItem[]>('/api/contracts');
  },

  uploadPDFContract: (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/contracts/upload-pdf', {
      method: 'POST',
      body: formData,
    });
  },
};
