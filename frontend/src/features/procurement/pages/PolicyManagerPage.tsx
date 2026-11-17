import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { usePolicy } from '../hooks/usePolicy';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { PolicyUploadPanel, PolicyDiffPanel } from '../components';

export const PolicyManagerPage: React.FC = () => {
  const {
    activeVersion,
    diff,
    previewText,
    previewFile,
    approvePolicy,
    isPreviewing,
    isApproving,
  } = usePolicy();

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={20} color="var(--accent-cyan)" />
            <span>Policy as Data Engine (Version {activeVersion})</span>
          </div>
        }
        subtitle="Policy rules are stored declaratively as data. Amendments compile into dynamic specification trees with zero code changes."
        action={
          <Badge variant="emerald">
            Active: v{activeVersion}
          </Badge>
        }
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem', marginTop: '0.5rem' }}>
          <PolicyUploadPanel
            onPreviewText={(text) => previewText(text)}
            onPreviewFile={(file) => previewFile(file)}
            isLoading={isPreviewing || isApproving}
          />

          <PolicyDiffPanel
            diff={diff}
            onApprove={(ver) => approvePolicy(ver)}
            isApproving={isApproving}
          />
        </div>
      </Card>
    </div>
  );
};
