import { useQuery } from '@tanstack/react-query';
import { supplierService } from '../services';
import { PreferredSuppliersResponse } from '../../../types';

export const SUPPLIERS_QUERY_KEY = ['suppliers', 'preferred'];

export function useSuppliers(targetDate: string, itemCode?: string) {
  const query = useQuery<PreferredSuppliersResponse>({
    queryKey: [...SUPPLIERS_QUERY_KEY, targetDate, itemCode || 'ALL'],
    queryFn: () => supplierService.getPreferredSuppliers(targetDate, itemCode),
    staleTime: 1000 * 60, // 1 minute
  });

  return {
    ...query,
    items: query.data?.items || {},
    exportUrl: supplierService.getExportUrl(targetDate),
  };
}
