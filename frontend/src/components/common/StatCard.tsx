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
  valueColor = '#fff',
}) => {
  return (
    <div className="card" style={{ marginBottom: 0, padding: '1.25rem', position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 500 }}>
          {label}
        </div>
        {icon && (
          <div style={{ color: 'var(--text-dim)', opacity: 0.8 }}>
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
