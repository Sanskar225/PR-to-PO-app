import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService } from '../services';
import { ContractItem } from '../../../types';
import { useToast } from '../../../context/ToastContext';

export const CONTRACTS_QUERY_KEY = ['contracts', 'list'];

export function useContracts() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const query = useQuery<ContractItem[]>({
    queryKey: CONTRACTS_QUERY_KEY,
    queryFn: () => contractService.getContracts(),
    staleTime: 1000 * 60, // 1 minute
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => contractService.uploadPDFContract(file),
    onSuccess: (data) => {
      success(data.message || 'Contract PDF extracted and registered successfully!', 'Contract Registered');
      queryClient.invalidateQueries({ queryKey: CONTRACTS_QUERY_KEY });
    },
    onError: (err: any) => {
      error(err.message || 'Failed to extract PDF contract', 'Upload Error');
    },
  });

  return {
    ...query,
    contracts: query.data || [],
    uploadPDFContract: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
  };
}
