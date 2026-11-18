import React from 'react';
import { FileText, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ParsedPR } from '../../../../types';
import { Card } from '../../../../components/common/Card';
import { Button } from '../../../../components/common/Button';
import { Badge } from '../../../../components/common/Badge';

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
          <FileText size={18} color="var(--accent-orange)" />
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
              <code style={{ fontWeight: 600 }}>
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
                {parsedPR.quantity !== null && parsedPR.quantity !== undefined
                  ? `${parsedPR.quantity} ${parsedPR.uom || 'units'}`
                  : 'Pending'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
                Delivery Date:
              </span>
              <strong>{parsedPR.need_by_date || 'Pending'}</strong>
            </div>
          </div>

          <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border-color)' }}>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem', marginBottom: '2px' }}>
              Extracted Description:
            </span>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {parsedPR.description || 'N/A'}
            </div>
          </div>

          {parsedPR.urgency && (
            <div style={{ marginTop: '0.5rem' }}>
              <Badge variant="amber" size="sm">
                FLAG: Urgent Requirement
              </Badge>
            </div>
          )}

          {parsedPR.missing_fields && parsedPR.missing_fields.length > 0 && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: '#fffbeb',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid #fde68a',
                fontSize: '0.8rem',
                color: '#b45309'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, marginBottom: '2px' }}>
                <AlertTriangle size={14} /> Missing required attributes:
              </div>
              <div>{parsedPR.missing_fields.join(', ')}</div>
            </div>
          )}

          <div style={{ marginTop: '1.25rem' }}>
            <Button
              variant="primary"
              onClick={onConfirm}
              disabled={!isComplete || isLoading}
              isLoading={isLoading}
              style={{ width: '100%' }}
              icon={<CheckCircle2 size={16} />}
            >
              Confirm and Route to Policy Engine
            </Button>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
          No active PR intake. Type your requirement or pick a quick prompt to begin.
        </div>
      )}
    </Card>
  );
};
