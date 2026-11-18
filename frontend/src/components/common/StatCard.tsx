import React, { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: ReactNode;
  valueColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon,
  valueColor = 'var(--text-main)',
}) => {
  return (
    <div className="card" style={{ marginBottom: 0, padding: '1.25rem', position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
          {label}
        </div>
        {icon && (
          <div style={{ color: 'var(--accent-orange)' }}>
            {icon}
          </div>
        )}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 800, color: valueColor, letterSpacing: '-0.02em' }}>
        {value}
      </div>
      {subtext && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
          {subtext}
        </div>
      )}
    </div>
  );
};
