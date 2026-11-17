import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { policyService } from '../services';
import { PolicyMetadata, PolicyAmendmentDiff } from '../../../types';
import { useToast } from '../../../context/ToastContext';

export const POLICY_QUERY_KEY = ['policy', 'current'];

export function usePolicy() {
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();
  const [diff, setDiff] = useState<PolicyAmendmentDiff | null>(null);

  const query = useQuery<PolicyMetadata>({
    queryKey: POLICY_QUERY_KEY,
    queryFn: () => policyService.getCurrentPolicy(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const previewTextMutation = useMutation({
    mutationFn: (text: string) => policyService.previewAmendmentText(text),
    onSuccess: (diffData) => {
      setDiff(diffData);
      info(`Proposed Version ${diffData.new_version} diff generated.`, 'Diff Preview Ready');
    },
    onError: (err: any) => {
      error(err.message || 'Failed to parse amendment text', 'Diff Generation Error');
    },
  });

  const previewFileMutation = useMutation({
    mutationFn: (file: File) => policyService.previewAmendmentFile(file),
    onSuccess: (diffData) => {
      setDiff(diffData);
      info(`Proposed Version ${diffData.new_version} diff generated from PDF.`, 'Diff Preview Ready');
    },
    onError: (err: any) => {
      error(err.message || 'Failed to parse amendment file', 'Diff Generation Error');
    },
  });

  const approveMutation = useMutation({
    mutationFn: (version: string) => policyService.approveAmendment(version),
    onSuccess: (_, version) => {
      success(`Policy Version ${version} is now active and enforced!`, 'Policy Activated');
      setDiff(null);
      queryClient.invalidateQueries({ queryKey: POLICY_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['buyer'] });
    },
    onError: (err: any) => {
      error(err.message || 'Failed to activate policy amendment', 'Activation Error');
    },
  });

  return {
    ...query,
    policy: query.data || null,
    activeVersion: query.data?.version || '5.0',
    diff,
    setDiff,
    previewText: previewTextMutation.mutateAsync,
    previewFile: previewFileMutation.mutateAsync,
    approvePolicy: approveMutation.mutateAsync,
    isPreviewing: previewTextMutation.isPending || previewFileMutation.isPending,
    isApproving: approveMutation.isPending,
  };
}
