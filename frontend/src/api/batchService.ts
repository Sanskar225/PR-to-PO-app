import { request } from './client';
import { BatchProcessResult } from '../types';

export const batchService = {
  processBatch: (file: File): Promise<BatchProcessResult> => {
    const formData = new FormData();
    formData.append('file', file);
    return request<BatchProcessResult>('/api/process-batch', {
      method: 'POST',
      body: formData,
    });
  },

  getDecisionsExportUrl: (): string => {
    return '/api/export-decisions';
  },
};
