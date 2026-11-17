import React from 'react';
import { FileText, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ParsedPR } from '../../types';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

interface PRPreviewCardProps {
  parsedPR: ParsedPR | null;
  onConfirm: () => void;
  isLoading: boolean;
}

export const PRPreviewCard: React.FC<PRPreviewCardProps> = ({
  parsedPR,
  onConfirm,
  isLoading,
}) => {
  const isComplete = parsedPR && (!parsedPR.missing_fields || parsedPR.missing_fields.length === 0);

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={18} color="var(--accent-cyan)" />
          <span>Structured PR Preview</span>
        </div>
      }
      action={
        parsedPR ? (
          <Badge variant={isComplete ? 'emerald' : 'amber'}>
            {isComplete ? 'Ready to Submit' : 'Incomplete'}
          </Badge>
        ) : null
      }
    >
      {parsedPR ? (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Item Code:
              </span>
              <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                {parsedPR.item_code || 'Resolving...'}
              </code>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Manufacturing Plant:
              </span>
              <strong>{parsedPR.plant || 'Pending'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Quantity:
              </span>
              <strong>
                {parsedPR.quantity ? `${parsedPR.quantity} ${parsedPR.uom || 'NOS'}` : 'Pending'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Urgency:
              </span>
              <Badge variant={parsedPR.urgency === 'Emergency' ? 'amber' : 'dim'} size="sm">
                {parsedPR.urgency || 'Normal'}
              </Badge>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Item Description:
              </span>
              <strong>{parsedPR.description || 'Pending'}</strong>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Need-By Date:
              </span>
              <strong>{parsedPR.need_by_date || 'Pending'}</strong>
            </div>
          </div>

          {parsedPR.missing_fields && parsedPR.missing_fields.length > 0 && (
            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.75rem 1rem',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                color: '#fbbf24',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <AlertTriangle size={15} style={{ flexShrink: 0 }} />
              <span>Missing attributes required by policy: <strong>{parsedPR.missing_fields.join(', ')}</strong></span>
            </div>
          )}

          {isComplete && (
            <Button
              variant="success"
              style={{ width: '100%', marginTop: '1.25rem' }}
              onClick={onConfirm}
              isLoading={isLoading}
              icon={<CheckCircle2 size={16} />}
            >
              Confirm & Submit PR
            </Button>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
          <p style={{ margin: 0 }}>Type your procurement requirement in the chat to auto-generate the PR preview card.</p>
        </div>
      )}
    </Card>
  );
};
