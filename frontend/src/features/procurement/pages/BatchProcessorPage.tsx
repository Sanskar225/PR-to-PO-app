import React from 'react';
import { FileSpreadsheet } from 'lucide-react';
import { useBatch } from '../hooks/useBatch';
import { useApp } from '../../../context/AppContext';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { BatchUploadPanel, BatchSummaryPanel, RouteDistributionPanel } from '../components';

export const BatchProcessorPage: React.FC = () => {
  const { processBatch, isProcessing, result, exportUrl } = useBatch();
  const { activePolicyVersion } = useApp();

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileSpreadsheet size={20} color="var(--accent-cyan)" />
            <span>Batch PR Processing & Blind-Test Engine</span>
          </div>
        }
        subtitle="Ingests multi-line PR CSV datasets, executes chronological clubbing, valuation cascade, and generates consolidated POs."
        action={
          <Badge variant="blue">
            Active Policy: v{activePolicyVersion}
          </Badge>
        }
      >
        <BatchUploadPanel
          onProcessFile={(file) => processBatch(file)}
          exportUrl={exportUrl}
          isProcessing={isProcessing}
        />

        {result && (
          <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
            <BatchSummaryPanel result={result} />
            <RouteDistributionPanel
              routeDistribution={result.route_distribution}
              policyVersion={result.policy_version_applied}
            />
          </div>
        )}
      </Card>
    </div>
  );
};
