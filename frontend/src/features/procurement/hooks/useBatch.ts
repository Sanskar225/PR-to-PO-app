import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { batchService } from '../services';
import { BatchProcessResult } from '../../../types';
import { useToast } from '../../../context/ToastContext';

export function useBatch() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();
  const [result, setResult] = useState<BatchProcessResult | null>(null);

  const processMutation = useMutation({
    mutationFn: (file: File) => batchService.processBatch(file),
    onSuccess: (data) => {
      setResult(data);
      success(
        `Batch executed: ${data.total_lines} lines grouped into ${data.unique_requirements} requirements (${data.consolidated_pos} POs) under Policy v${data.policy_version_applied}`,
        'Batch Completed'
      );
      queryClient.invalidateQueries({ queryKey: ['buyer'] });
    },
    onError: (err: any) => {
      error(err.message || 'Batch execution failed', 'Batch Processing Error');
    },
  });

  return {
    processBatch: processMutation.mutateAsync,
    isProcessing: processMutation.isPending,
    result,
    setResult,
    exportUrl: batchService.getDecisionsExportUrl(),
  };
}
