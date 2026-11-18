import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Award, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import { RankedSupplier } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { Pagination } from '../../../../components/common/Pagination';
import { formatINR } from '../../lib/formatters';

interface SupplierRankingTablePanelProps {
  entries: Array<[string, RankedSupplier[]]>;
  isLoading?: boolean;
}

type SortField = 'item_code' | 'composite_score' | 'reference_price' | 'on_time_pct' | 'quality_rating';
type SortOrder = 'asc' | 'desc';

export const SupplierRankingTablePanel: React.FC<SupplierRankingTablePanelProps> = ({ 
  entries,
  isLoading = false 
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [sortField, setSortField] = useState<SortField>('item_code');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Sort entries
  const sortedEntries = useMemo(() => {
    const list = [...entries];
    list.sort((a, b) => {
      const itemCodeA = a[0];
      const itemCodeB = b[0];
      const topSuppA = a[1][0];
      const topSuppB = b[1][0];

      if (sortField === 'item_code') {
        const cmp = itemCodeA.localeCompare(itemCodeB);
        return sortOrder === 'asc' ? cmp : -cmp;
      }

      let valA = 0;
      let valB = 0;
      if (sortField === 'composite_score') {
        valA = topSuppA?.composite_score || 0;
        valB = topSuppB?.composite_score || 0;
      } else if (sortField === 'reference_price') {
        valA = topSuppA?.reference_price || 0;
        valB = topSuppB?.reference_price || 0;
      } else if (sortField === 'on_time_pct') {
        valA = topSuppA?.on_time_pct || 0;
        valB = topSuppB?.on_time_pct || 0;
      } else if (sortField === 'quality_rating') {
        valA = topSuppA?.quality_rating || 0;
        valB = topSuppB?.quality_rating || 0;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [entries, sortField, sortOrder]);

  // Paginated slice
  const paginatedEntries = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedEntries.slice(start, start + pageSize);
  }, [sortedEntries, currentPage, pageSize]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown size={13} style={{ opacity: 0.4 }} />;
    return sortOrder === 'asc' ? (
      <ArrowUp size={13} style={{ color: 'var(--accent-orange)' }} />
    ) : (
      <ArrowDown size={13} style={{ color: 'var(--accent-orange)' }} />
    );
  };

  if (isLoading && entries.length === 0) {
    return (
      <div style={{ padding: '1.5rem', background: '#ffffff', borderRadius: 'var(--radius-lg)' }}>
        {[...Array(6)].map((_, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
            <div className="skeleton-box" style={{ width: '80%' }} />
            <div className="skeleton-box" style={{ width: '40%' }} />
            <div className="skeleton-box" style={{ width: '70%' }} />
            <div className="skeleton-box" style={{ width: '90%' }} />
            <div className="skeleton-box" style={{ width: '60%' }} />
            <div className="skeleton-box" style={{ width: '50%' }} />
            <div className="skeleton-box" style={{ width: '40%' }} />
          </div>
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          padding: '4rem 1.5rem',
          color: 'var(--text-dim)',
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px dashed var(--border-color)',
        }}
      >
        <Award size={32} style={{ color: 'var(--accent-orange)', margin: '0 auto 0.75rem auto' }} />
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
          No Suppliers Found
        </h4>
        <p style={{ fontSize: '0.85rem' }}>No item codes or suppliers match the current search filter.</p>
      </div>
    );
  }

  return (
    <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
      <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th className="th-sortable" onClick={() => handleSort('item_code')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Item Code</span>
                  {getSortIcon('item_code')}
                </div>
              </th>
              <th>Rank</th>
              <th>Supplier ID</th>
              <th>Supplier Name</th>
              <th className="th-sortable" onClick={() => handleSort('reference_price')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Reference Price</span>
                  {getSortIcon('reference_price')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('composite_score')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Composite Score</span>
                  {getSortIcon('composite_score')}
                </div>
              </th>
              <th>Order History (548d)</th>
              <th>Recency Score</th>
              <th>Contract</th>
              <th className="th-sortable" onClick={() => handleSort('on_time_pct')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>On-Time %</span>
                  {getSortIcon('on_time_pct')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('quality_rating')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Quality</span>
                  {getSortIcon('quality_rating')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedEntries.map(([itemCode, suppliers]) =>
              suppliers.map((supp, idx) => {
                const isTop = supp.rank === 1;

                return (
                  <tr key={`${itemCode}-${supp.supplier_id}`} className={isTop ? 'selected-row' : ''}>
                    {idx === 0 ? (
                      <td
                        rowSpan={suppliers.length}
                        style={{
                          verticalAlign: 'top',
                          borderRight: '1px solid var(--border-color)',
                          fontWeight: 700,
                          background: '#fafafa',
                        }}
                      >
                        <code style={{ fontSize: '0.85rem' }}>{itemCode}</code>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                          {suppliers.length} Supplier{suppliers.length > 1 ? 's' : ''}
                        </div>
                      </td>
                    ) : null}
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '26px',
                          height: '26px',
                          borderRadius: '50%',
                          background: isTop ? 'var(--accent-orange)' : '#f4f4f5',
                          color: isTop ? '#ffffff' : 'var(--text-main)',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                        }}
                      >
                        {supp.rank}
                      </span>
                    </td>
                    <td>
                      <code>{supp.supplier_id}</code>
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-main)' }}>{supp.supplier_name}</strong>
                    </td>
                    <td style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>
                      {supp.reference_price ? formatINR(supp.reference_price) : 'N/A'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <strong style={{ color: 'var(--text-main)', minWidth: '35px' }}>
                          {supp.composite_score.toFixed(2)}
                        </strong>
                        <div
                          style={{
                            flex: 1,
                            maxWidth: '70px',
                            height: '6px',
                            background: '#f4f4f5',
                            borderRadius: '3px',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              width: `${Math.min(100, Math.max(0, supp.composite_score * 100))}%`,
                              height: '100%',
                              background: isTop ? 'var(--accent-orange)' : '#94a3b8',
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span>{supp.po_count_548d} POs</span>
                    </td>
                    <td>
                      <span>{supp.recency_score !== undefined ? supp.recency_score.toFixed(2) : '0.00'}</span>
                    </td>
                    <td>
                      {supp.has_contract ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#16a34a', fontSize: '0.8rem', fontWeight: 600 }}>
                          <CheckCircle size={14} /> Yes
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                          <XCircle size={14} /> No
                        </span>
                      )}
                    </td>
                    <td>
                      <strong style={{ color: supp.on_time_pct && supp.on_time_pct >= 95 ? '#16a34a' : 'var(--text-main)' }}>
                        {supp.on_time_pct ? `${supp.on_time_pct}%` : 'N/A'}
                      </strong>
                    </td>
                    <td>
                      <span>{supp.quality_rating ? `${supp.quality_rating} / 5.0` : 'N/A'}</span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <Pagination
        currentPage={currentPage}
        totalItems={sortedEntries.length}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        onPageSizeChange={setPageSize}
        pageSizeOptions={[10, 15, 25, 50]}
      />
    </div>
  );
};
