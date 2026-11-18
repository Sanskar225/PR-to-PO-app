import React from 'react';
import { Layers } from 'lucide-react';
import { Badge } from '../../../../components/common/Badge';

interface RouteDistributionPanelProps {
  routeDistribution: Record<string, number>;
  policyVersion: string;
}

export const RouteDistributionPanel: React.FC<RouteDistributionPanelProps> = ({
  routeDistribution,
  policyVersion,
}) => {
  return (
    <div style={{ background: '#ffffff', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
      <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-main)' }}>
        <Layers size={16} color="var(--accent-orange)" />
        <span>Route Distribution Breakdown (Policy v{policyVersion}):</span>
      </div>
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {Object.entries(routeDistribution).map(([route, count]) => (
          <div
            key={route}
            style={{
              padding: '0.5rem 0.85rem',
              background: '#fafafa',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'center'
            }}
          >
            <Badge route={route} size="sm" />
            <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>{count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
};
