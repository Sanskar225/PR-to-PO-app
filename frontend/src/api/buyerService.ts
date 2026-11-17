import { request } from './client';
import { BuyerWorkspaceData } from '../types';

export interface ApproveRequirementPayload {
  group_id: string;
  buyer_name?: string;
}

export interface OverrideRequirementPayload {
  group_id: string;
  override_route: string;
  override_comment: string;
  buyer_name?: string;
}

export const buyerService = {
  getRequirements: (route?: string, plant?: string): Promise<BuyerWorkspaceData> => {
    const params = new URLSearchParams();
    if (route && route !== 'ALL') params.append('route', route);
    if (plant && plant !== 'ALL') params.append('plant', plant);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return request<BuyerWorkspaceData>(`/api/buyer/requirements${queryString}`);
  },

  approveRequirement: (payload: ApproveRequirementPayload): Promise<any> => {
    return request('/api/buyer/approve', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  overrideRequirement: (payload: OverrideRequirementPayload): Promise<any> => {
    return request('/api/buyer/override', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
