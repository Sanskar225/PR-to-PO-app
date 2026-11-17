import { useQuery } from '@tanstack/react-query';
import { contractService } from '../services';
import { ContractItem } from '../../../types';

export const CONTRACTS_QUERY_KEY = ['contracts', 'list'];

export function useContracts() {
  const query = useQuery<ContractItem[]>({
    queryKey: CONTRACTS_QUERY_KEY,
    queryFn: () => contractService.getContracts(),
    staleTime: 1000 * 60, // 1 minute
  });

  return {
    ...query,
    contracts: query.data || [],
  };
}
