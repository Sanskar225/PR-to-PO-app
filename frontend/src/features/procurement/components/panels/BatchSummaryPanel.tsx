import React from 'react';
import { BatchProcessResult } from '../../../../types';
import { formatCompactINR } from '../../lib/formatters';

interface BatchSummaryPanelProps {
  result: BatchProcessResult;
}

export const BatchSummaryPanel: React.FC<BatchSummaryPanelProps> = ({ result }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
      <div style={{ padding: '1.25rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>PR Lines Processed</div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)' }}>{result.total_lines}</div>
      </div>

      <div style={{ padding: '1.25rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>Requirement Groups</div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-orange)' }}>{result.unique_requirements}</div>
      </div>

      <div style={{ padding: '1.25rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>Consolidated POs (24h)</div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#16a34a' }}>{result.consolidated_pos}</div>
      </div>

      <div style={{ padding: '1.25rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>Total Spend</div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-orange)' }}>
          {formatCompactINR(result.total_value_inr)}
        </div>
      </div>
    </div>
  );
};
