import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, FileText } from 'lucide-react';
import { ContractItem } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { Pagination } from '../../../../components/common/Pagination';
import { formatINR } from '../../lib/formatters';

interface ContractsTablePanelProps {
  contracts: ContractItem[];
  isLoading?: boolean;
}

type SortField = 'contract_id' | 'supplier_name' | 'value_cap' | 'consumed_value' | 'remaining';
type SortOrder = 'asc' | 'desc';

export const ContractsTablePanel: React.FC<ContractsTablePanelProps> = ({ 
  contracts,
  isLoading = false 
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortField, setSortField] = useState<SortField>('contract_id');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Sorting
  const sortedContracts = useMemo(() => {
    const list = [...contracts];
    list.sort((a, b) => {
      let valA: any = a[sortField as keyof ContractItem];
      let valB: any = b[sortField as keyof ContractItem];

      if (sortField === 'remaining') {
        valA = Math.max(0, a.value_cap - a.consumed_value);
        valB = Math.max(0, b.value_cap - b.consumed_value);
      } else if (sortField === 'value_cap' || sortField === 'consumed_value') {
        valA = Number(valA || 0);
        valB = Number(valB || 0);
      } else if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = (valB || '').toLowerCase();
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [contracts, sortField, sortOrder]);

  // Paginated slice
  const paginatedContracts = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedContracts.slice(start, start + pageSize);
  }, [sortedContracts, currentPage, pageSize]);

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

  if (isLoading && contracts.length === 0) {
    return (
      <div style={{ padding: '1.5rem', background: '#ffffff', borderRadius: 'var(--radius-lg)' }}>
        {[...Array(5)].map((_, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
            <div className="skeleton-box" style={{ width: '80%' }} />
            <div className="skeleton-box" style={{ width: '60%' }} />
            <div className="skeleton-box" style={{ width: '70%' }} />
            <div className="skeleton-box" style={{ width: '50%' }} />
            <div className="skeleton-box" style={{ width: '90%' }} />
            <div className="skeleton-box" style={{ width: '40%' }} />
          </div>
        ))}
      </div>
    );
  }

  if (contracts.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1.5rem', color: 'var(--text-dim)', background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px dashed var(--border-color)' }}>
        <FileText size={32} style={{ color: 'var(--accent-orange)', margin: '0 auto 0.75rem auto' }} />
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
          No Contracts Found in Register
        </h4>
        <p style={{ fontSize: '0.85rem' }}>Upload a signed contract PDF or ensure contracts.csv is seeded.</p>
      </div>
    );
  }

  return (
    <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', overflow: 'hidden', marginTop: '0.5rem' }}>
      <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th className="th-sortable" onClick={() => handleSort('contract_id')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Contract ID</span>
                  {getSortIcon('contract_id')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('supplier_name')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Supplier</span>
                  {getSortIcon('supplier_name')}
                </div>
              </th>
              <th>Validity Window</th>
              <th className="th-sortable" onClick={() => handleSort('value_cap')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Ceiling Cap (INR)</span>
                  {getSortIcon('value_cap')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('consumed_value')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Consumed Spend</span>
                  {getSortIcon('consumed_value')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('remaining')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Remaining Headroom</span>
                  {getSortIcon('remaining')}
                </div>
              </th>
              <th>Contract Source</th>
            </tr>
          </thead>
          <tbody>
            {paginatedContracts.map((c) => {
              const pct = Math.min(100, Math.round((c.consumed_value / c.value_cap) * 100));
              const remaining = Math.max(0, c.value_cap - c.consumed_value);
              const isNearLimit = pct > 85;

              return (
                <tr key={c.contract_id}>
                  <td>
                    <code style={{ fontWeight: 700 }}>{c.contract_id}</code>
                  </td>
                  <td>
                    <strong style={{ color: 'var(--text-main)' }}>{c.supplier_name}</strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>
                      ID: {c.supplier_id}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {c.start_date} → {c.end_date}
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {formatINR(c.value_cap)}
                  </td>
                  <td>
                    <div>
                      {formatINR(c.consumed_value)}
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '4px' }}>
                        ({pct}%)
                      </span>
                    </div>
                    <div style={{ width: '120px', height: '6px', background: '#f4f4f5', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: isNearLimit ? '#dc2626' : 'var(--accent-orange)',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </td>
                  <td style={{ fontWeight: 700, color: isNearLimit ? '#dc2626' : 'var(--accent-orange)' }}>
                    {formatINR(remaining)}
                  </td>
                  <td>
                    <Badge variant={c.is_pdf_extracted ? 'emerald' : 'dim'} size="sm">
                      {c.is_pdf_extracted ? 'PDF Ingested' : 'Master CSV'}
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <Pagination
        currentPage={currentPage}
        totalItems={sortedContracts.length}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        onPageSizeChange={setPageSize}
        pageSizeOptions={[5, 10, 20]}
      />
    </div>
  );
};
