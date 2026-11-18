import React from 'react';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { PolicyAmendmentDiff } from '../../../../types';
import { Button } from '../../../../components/common/Button';

interface PolicyDiffPanelProps {
  diff: PolicyAmendmentDiff | null;
  onApprove: (version: string) => Promise<void>;
  isApproving: boolean;
}

export const PolicyDiffPanel: React.FC<PolicyDiffPanelProps> = ({
  diff,
  onApprove,
  isApproving,
}) => {
  return (
    <div>
      <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-main)' }}>
        Diff & Specification Impact Preview
      </h4>

      {diff ? (
        <div
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            animation: 'fadeIn 0.25s ease-out'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-dim)' }}>
              v{diff.base_version}
            </span>
            <ArrowRight size={15} color="var(--accent-orange)" />
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-orange)' }}>
              Proposed v{diff.new_version}
            </span>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Target Effective Date: <strong>{diff.effective_date}</strong>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.825rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-main)' }}>
              Detected Policy Clause Changes:
            </div>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              {diff.summary_of_changes.map((change, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>
                  <strong style={{ color: 'var(--accent-orange)' }}>•</strong> {change}
                </li>
              ))}
            </ul>
          </div>

          <Button
            variant="primary"
            style={{ width: '100%' }}
            onClick={() => onApprove(diff.new_version)}
            isLoading={isApproving}
            icon={<CheckCircle2 size={16} />}
          >
            Approve & Activate Version {diff.new_version}
          </Button>
        </div>
      ) : (
        <div
          style={{
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            color: 'var(--text-dim)',
            background: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px dashed var(--border-color)',
            fontSize: '0.85rem'
          }}
        >
          Upload an amendment PDF or paste revision text on the left to review the computed diff and specification rules before activation.
        </div>
      )}
    </div>
  );
};
