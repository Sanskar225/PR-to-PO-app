import React from 'react';
import { RankedSupplier } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { formatINR } from '../../lib/formatters';

interface SupplierRankingTablePanelProps {
  entries: Array<[string, RankedSupplier[]]>;
}

export const SupplierRankingTablePanel: React.FC<SupplierRankingTablePanelProps> = ({ entries }) => {
  if (entries.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-dim)', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-color)' }}>
        No suppliers match the search query.
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Item Code</th>
            <th>Rank</th>
            <th>Supplier ID</th>
            <th>Supplier Name</th>
            <th>Reference Price</th>
            <th>Composite Score</th>
            <th>POs (548d)</th>
            <th>Recency</th>
            <th>Contract</th>
            <th>On-Time %</th>
            <th>Quality</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([itemCode, suppliers]) =>
            suppliers.map((supp, idx) => (
              <tr key={`${itemCode}-${supp.supplier_id}`}>
                {idx === 0 ? (
                  <td
                    rowSpan={suppliers.length}
                    style={{ verticalAlign: 'top', borderRight: '1px solid var(--border-color)', fontWeight: 700 }}
                  >
                    <code>{itemCode}</code>
                  </td>
                ) : null}
                <td>
                  <Badge variant={supp.rank === 1 ? 'emerald' : 'dim'} size="sm">
                    #{supp.rank}
                  </Badge>
                </td>
                <td>
                  <code>{supp.supplier_id}</code>
                </td>
                <td>
                  <strong>{supp.supplier_name}</strong>
                </td>
                <td style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>
                  {supp.reference_price ? formatINR(supp.reference_price) : 'N/A'}
                </td>
                <td>
                  <strong style={{ color: 'var(--text-main)' }}>{supp.composite_score.toFixed(2)}</strong>
                </td>
                <td>{supp.po_count_548d}</td>
                <td>{supp.recency_score !== undefined ? supp.recency_score.toFixed(2) : '0.00'}</td>
                <td>
                  <Badge variant={supp.has_contract ? 'emerald' : 'dim'} size="sm">
                    {supp.has_contract ? 'Yes' : 'No'}
                  </Badge>
                </td>
                <td>{supp.on_time_pct ? `${supp.on_time_pct}%` : 'N/A'}</td>
                <td>{supp.quality_rating ? `${supp.quality_rating}/5` : 'N/A'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
