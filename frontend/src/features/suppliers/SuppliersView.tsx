import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Award, Download, Calendar, Search, RefreshCw } from 'lucide-react';
import { RankedSupplier } from '../../types';
import { supplierService } from '../../api/supplierService';
import { useToast } from '../../context/ToastContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

export const SuppliersView: React.FC = () => {
  const [targetDate, setTargetDate] = useState('2026-11-01');
  const [preferredItems, setPreferredItems] = useState<Record<string, RankedSupplier[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const { error } = useToast();

  const fetchSuppliers = useCallback(async (date: string) => {
    setIsLoading(true);
    try {
      const data = await supplierService.getPreferredSuppliers(date);
      setPreferredItems(data.items || {});
    } catch (err: any) {
      error(err.message || 'Failed to load preferred suppliers', 'Supplier Directory');
    } finally {
      setIsLoading(false);
    }
  }, [error]);

  useEffect(() => {
    fetchSuppliers(targetDate);
  }, [fetchSuppliers, targetDate]);

  const filteredEntries = useMemo(() => {
    const entries = Object.entries(preferredItems);
    if (!searchQuery) return entries.slice(0, 45);

    const q = searchQuery.toLowerCase();
    return entries.filter(([itemCode, suppliers]) => {
      if (itemCode.toLowerCase().includes(q)) return true;
      return suppliers.some(s => s.supplier_name.toLowerCase().includes(q) || s.supplier_id.toLowerCase().includes(q));
    }).slice(0, 45);
  }, [preferredItems, searchQuery]);

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={20} color="var(--accent-amber)" />
            <span>Preferred Supplier Directory (Policy Section 6)</span>
          </div>
        }
        subtitle="Analytical multi-criteria ranking model evaluating 548-day order history, recency, active contracts, on-time delivery, and quality."
        action={
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Calendar size={15} color="var(--text-dim)" />
              <input
                type="date"
                className="chat-input"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                style={{ padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
              />
            </div>

            <a
              href={supplierService.getExportUrl(targetDate)}
              download="preferred_suppliers.csv"
              className="btn btn-success btn-sm"
              style={{ textDecoration: 'none' }}
            >
              <Download size={14} />
              <span>Export CSV</span>
            </a>
          </div>
        }
      >
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', margin: '0.5rem 0 1.25rem 0' }}>
          <div style={{ position: 'relative', maxWidth: '320px', width: '100%' }}>
            <input
              type="text"
              placeholder="Search Item Code or Supplier Name..."
              className="chat-input"
              style={{ width: '100%', paddingLeft: '2.25rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Search
              size={15}
              style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }}
            />
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchSuppliers(targetDate)}
            isLoading={isLoading}
            icon={<RefreshCw size={14} />}
          >
            Refresh Rankings
          </Button>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Item Code</th>
                <th>Rank</th>
                <th>Supplier ID</th>
                <th>Supplier Name</th>
                <th>Reference Price</th>
                <th>Score</th>
                <th>POs (548d)</th>
                <th>Recency</th>
                <th>Contract</th>
                <th>On-Time %</th>
                <th>Quality</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map(([itemCode, suppliers]) =>
                suppliers.map((supp, idx) => (
                  <tr key={`${itemCode}-${supp.supplier_id}`}>
                    {idx === 0 ? (
                      <td
                        rowSpan={suppliers.length}
                        style={{ verticalAlign: 'top', borderRight: '1px solid var(--border-color)', fontWeight: 700 }}
                      >
                        <code style={{ color: 'var(--accent-cyan)' }}>{itemCode}</code>
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
                    <td style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>
                      ₹{supp.reference_price}
                    </td>
                    <td>
                      <strong style={{ color: '#fff' }}>{supp.composite_score}</strong>
                    </td>
                    <td>{supp.po_count_548d}</td>
                    <td>{supp.recency_score}</td>
                    <td>
                      {supp.has_contract ? (
                        <span style={{ color: '#34d399', fontWeight: 600 }}>Active</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>None</span>
                      )}
                    </td>
                    <td>{supp.on_time_pct}%</td>
                    <td>{supp.quality_rating} / 5.0</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
