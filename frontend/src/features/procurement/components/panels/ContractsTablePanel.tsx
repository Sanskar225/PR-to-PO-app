import React from 'react';
import { ContractItem } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { formatINR } from '../../lib/formatters';

interface ContractsTablePanelProps {
  contracts: ContractItem[];
}

export const ContractsTablePanel: React.FC<ContractsTablePanelProps> = ({ contracts }) => {
  if (contracts.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-dim)', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-color)' }}>
        No contracts found in register.
      </div>
    );
  }

  return (
    <div className="table-wrapper" style={{ marginTop: '0.5rem' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Contract ID</th>
            <th>Supplier</th>
            <th>Validity Window</th>
            <th>Ceiling Cap (INR)</th>
            <th>Consumed Spend</th>
            <th>Remaining Headroom</th>
            <th>Contract Source</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((c) => {
            const pct = Math.min(100, Math.round((c.consumed_value / c.value_cap) * 100));
            const remaining = Math.max(0, c.value_cap - c.consumed_value);
            const isNearLimit = pct > 85;

            return (
              <tr key={c.contract_id}>
                <td>
                  <code style={{ fontWeight: 600 }}>{c.contract_id}</code>
                </td>
                <td>
                  <strong>{c.supplier_name}</strong>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>
                    ID: {c.supplier_id}
                  </span>
                </td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {c.start_date} → {c.end_date}
                </td>
                <td style={{ fontWeight: 600 }}>
                  {formatINR(c.value_cap)}
                </td>
                <td>
                  <div>
                    {formatINR(c.consumed_value)}
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '4px' }}>
                      ({pct}%)
                    </span>
                  </div>
                  <div style={{ width: '100px', height: '5px', background: '#f4f4f5', borderRadius: '4px', marginTop: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: isNearLimit ? '#dc2626' : 'var(--accent-orange)' }} />
                  </div>
                </td>
                <td style={{ fontWeight: 700, color: isNearLimit ? '#dc2626' : 'var(--accent-orange)' }}>
                  {formatINR(remaining)}
                </td>
                <td>
                  <Badge variant={c.is_pdf_extracted ? 'emerald' : 'dim'} size="sm">
                    {c.is_pdf_extracted ? 'PDF Ingested' : 'CSV Master'}
                  </Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
