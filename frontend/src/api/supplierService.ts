import { request } from './client';
import { PreferredSuppliersResponse } from '../types';

export const supplierService = {
  getPreferredSuppliers: (date: string, itemCode?: string): Promise<PreferredSuppliersResponse> => {
    const params = new URLSearchParams({ date });
    if (itemCode) params.append('item_code', itemCode);
    return request<PreferredSuppliersResponse>(`/api/suppliers/preferred?${params.toString()}`);
  },

  getExportUrl: (date: string): string => {
    return `/api/suppliers/preferred/export?date=${encodeURIComponent(date)}`;
  },
};
