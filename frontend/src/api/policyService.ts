import { request } from './client';
import { PolicyMetadata, PolicyAmendmentDiff } from '../types';

export const policyService = {
  getCurrentPolicy: (): Promise<PolicyMetadata> => {
    return request<PolicyMetadata>('/api/policy/current');
  },

  previewAmendmentText: (amendmentText: string): Promise<PolicyAmendmentDiff> => {
    return request<PolicyAmendmentDiff>('/api/policy/amend-text', {
      method: 'POST',
      body: JSON.stringify({ amendment_text: amendmentText }),
    });
  },

  previewAmendmentFile: (file: File): Promise<PolicyAmendmentDiff> => {
    const formData = new FormData();
    formData.append('file', file);
    return request<PolicyAmendmentDiff>('/api/policy/amend-upload', {
      method: 'POST',
      body: formData,
    });
  },

  approveAmendment: (version: string): Promise<any> => {
    return request('/api/policy/approve', {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  },
};
