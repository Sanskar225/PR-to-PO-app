import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { buyerService, ApproveRequirementPayload, OverrideRequirementPayload } from '../services';
import { BuyerWorkspaceData } from '../../../types';
import { useToast } from '../../../context/ToastContext';

export const BUYER_QUERY_KEY = ['buyer', 'requirements'];

export function useBuyer(route?: string, plant?: string) {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const query = useQuery<BuyerWorkspaceData>({
    queryKey: [...BUYER_QUERY_KEY, route || 'ALL', plant || 'ALL'],
    queryFn: () => buyerService.getRequirements(route, plant),
    staleTime: 1000 * 30, // 30 seconds
  });

  const approveMutation = useMutation({
    mutationFn: (payload: ApproveRequirementPayload) => buyerService.approveRequirement(payload),
    onSuccess: (_, variables) => {
      success(`Requirement ${variables.group_id} approved successfully!`, 'Requirement Approved');
      queryClient.invalidateQueries({ queryKey: ['buyer'] });
    },
    onError: (err: any) => {
      error(err.message || 'Failed to approve requirement', 'Approval Error');
    },
  });

  const overrideMutation = useMutation({
    mutationFn: (payload: OverrideRequirementPayload) => buyerService.overrideRequirement(payload),
    onSuccess: (_, variables) => {
      success(`Requirement ${variables.group_id} re-routed to ${variables.override_route}`, 'Decision Overridden');
      queryClient.invalidateQueries({ queryKey: ['buyer'] });
    },
    onError: (err: any) => {
      error(err.message || 'Failed to override requirement', 'Override Error');
    },
  });

  return {
    ...query,
    requirements: query.data?.requirements || [],
    summary: query.data?.summary || null,
    approveRequirement: approveMutation.mutateAsync,
    isApproving: approveMutation.isPending,
    overrideRequirement: overrideMutation.mutateAsync,
    isOverriding: overrideMutation.isPending,
  };
}
