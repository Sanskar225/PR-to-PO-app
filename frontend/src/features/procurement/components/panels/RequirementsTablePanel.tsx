import React, { useState, useMemo } from 'react';
import { 
  Check, Edit3, ChevronDown, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown,
  Info, Clock, Shield, FileText, CheckCircle2
} from 'lucide-react';
import { RequirementDecision, RouteType } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { Button } from '../../../../components/common/Button';
import { Pagination } from '../../../../components/common/Pagination';
import { formatINR } from '../../lib/formatters';

interface RequirementsTablePanelProps {
  requirements: RequirementDecision[];
  onApprove: (groupId: string) => void;
  onOpenOverride: (req: RequirementDecision) => void;
  isLoading: boolean;
}

type SortField = 'group_id' | 'resolved_item_code' | 'route' | 'group_value_inr' | 'status';
type SortOrder = 'asc' | 'desc';

export const RequirementsTablePanel: React.FC<RequirementsTablePanelProps> = ({
  requirements,
  onApprove,
  onOpenOverride,
  isLoading,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortField, setSortField] = useState<SortField>('group_value_inr');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'OVERRIDDEN'>('ALL');

  // Status counts for quick filter tabs
  const statusCounts = useMemo(() => {
    let pending = 0;
    let approved = 0;
    let overridden = 0;
    requirements.forEach((r) => {
      if (r.status === 'APPROVED') approved++;
      else if (r.status === 'OVERRIDDEN') overridden++;
      else pending++;
    });
    return { all: requirements.length, pending, approved, overridden };
  }, [requirements]);

  // Filter by quick status tabs
  const filteredByStatus = useMemo(() => {
    if (statusFilter === 'ALL') return requirements;
    if (statusFilter === 'APPROVED') return requirements.filter((r) => r.status === 'APPROVED');
    if (statusFilter === 'OVERRIDDEN') return requirements.filter((r) => r.status === 'OVERRIDDEN');
    return requirements.filter((r) => r.status !== 'APPROVED' && r.status !== 'OVERRIDDEN');
  }, [requirements, statusFilter]);

  // Sorting
  const sortedRequirements = useMemo(() => {
    const list = [...filteredByStatus];
    list.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'group_value_inr') {
        aVal = a.group_value_inr || 0;
        bVal = b.group_value_inr || 0;
      } else if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (bVal || '').toLowerCase();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [filteredByStatus, sortField, sortOrder]);

  // Pagination slice
  const paginatedRequirements = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedRequirements.slice(start, start + pageSize);
  }, [sortedRequirements, currentPage, pageSize]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const toggleExpand = (groupId: string) => {
    setExpandedGroupId(prev => (prev === groupId ? null : groupId));
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown size={13} style={{ opacity: 0.4 }} />;
    return sortOrder === 'asc' ? (
      <ArrowUp size={13} style={{ color: 'var(--accent-orange)' }} />
    ) : (
      <ArrowDown size={13} style={{ color: 'var(--accent-orange)' }} />
    );
  };

  if (isLoading && requirements.length === 0) {
    return (
      <div className="table-wrapper" style={{ padding: '1.5rem' }}>
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

  if (requirements.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          padding: '4rem 1.5rem',
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px dashed var(--border-color)',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'var(--accent-orange-light)',
            color: 'var(--accent-orange)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
          }}
        >
          <FileText size={22} />
        </div>
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
          No Requirements in Queue
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', maxWidth: '420px', margin: '0 auto' }}>
          Requisitions are grouped automatically upon batch ingestion or chat submission. Go to the Batch Processor or Chat Intake tab to evaluate requisitions.
        </p>
      </div>
    );
  }

  return (
    <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
      {/* Quick Status Filter Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          padding: '0.75rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          background: '#fafafa',
          overflowX: 'auto',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dim)', marginRight: '0.5rem' }}>
          Filter by Status:
        </span>

        <button
          type="button"
          onClick={() => { setStatusFilter('ALL'); setCurrentPage(1); }}
          className={`chip ${statusFilter === 'ALL' ? 'active' : ''}`}
          style={{
            background: statusFilter === 'ALL' ? 'var(--accent-orange)' : '#ffffff',
            color: statusFilter === 'ALL' ? '#ffffff' : 'var(--text-main)',
            border: `1px solid ${statusFilter === 'ALL' ? 'var(--accent-orange)' : 'var(--border-color)'}`,
            fontWeight: statusFilter === 'ALL' ? 700 : 500,
          }}
        >
          All ({statusCounts.all})
        </button>

        <button
          type="button"
          onClick={() => { setStatusFilter('PENDING'); setCurrentPage(1); }}
          className={`chip ${statusFilter === 'PENDING' ? 'active' : ''}`}
          style={{
            background: statusFilter === 'PENDING' ? 'var(--accent-orange)' : '#ffffff',
            color: statusFilter === 'PENDING' ? '#ffffff' : 'var(--text-main)',
            border: `1px solid ${statusFilter === 'PENDING' ? 'var(--accent-orange)' : 'var(--border-color)'}`,
            fontWeight: statusFilter === 'PENDING' ? 700 : 500,
          }}
        >
          Pending Review ({statusCounts.pending})
        </button>

        <button
          type="button"
          onClick={() => { setStatusFilter('APPROVED'); setCurrentPage(1); }}
          className={`chip ${statusFilter === 'APPROVED' ? 'active' : ''}`}
          style={{
            background: statusFilter === 'APPROVED' ? 'var(--accent-orange)' : '#ffffff',
            color: statusFilter === 'APPROVED' ? '#ffffff' : 'var(--text-main)',
            border: `1px solid ${statusFilter === 'APPROVED' ? 'var(--accent-orange)' : 'var(--border-color)'}`,
            fontWeight: statusFilter === 'APPROVED' ? 700 : 500,
          }}
        >
          Approved POs ({statusCounts.approved})
        </button>

        <button
          type="button"
          onClick={() => { setStatusFilter('OVERRIDDEN'); setCurrentPage(1); }}
          className={`chip ${statusFilter === 'OVERRIDDEN' ? 'active' : ''}`}
          style={{
            background: statusFilter === 'OVERRIDDEN' ? 'var(--accent-orange)' : '#ffffff',
            color: statusFilter === 'OVERRIDDEN' ? '#ffffff' : 'var(--text-main)',
            border: `1px solid ${statusFilter === 'OVERRIDDEN' ? 'var(--accent-orange)' : 'var(--border-color)'}`,
            fontWeight: statusFilter === 'OVERRIDDEN' ? 700 : 500,
          }}
        >
          Overridden ({statusCounts.overridden})
        </button>
      </div>

      {/* Main Table */}
      <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th className="th-sortable" onClick={() => handleSort('group_id')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Group ID</span>
                  {getSortIcon('group_id')}
                </div>
              </th>
              <th>PR Lines</th>
              <th className="th-sortable" onClick={() => handleSort('resolved_item_code')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Item</span>
                  {getSortIcon('resolved_item_code')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('route')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Route</span>
                  {getSortIcon('route')}
                </div>
              </th>
              <th>Assigned Supplier</th>
              <th className="th-sortable" onClick={() => handleSort('group_value_inr')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Value (INR)</span>
                  {getSortIcon('group_value_inr')}
                </div>
              </th>
              <th className="th-sortable" onClick={() => handleSort('status')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Status</span>
                  {getSortIcon('status')}
                </div>
              </th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedRequirements.map((req) => {
              const isExpanded = expandedGroupId === req.group_id;

              return (
                <React.Fragment key={req.group_id}>
                  <tr
                    className={isExpanded ? 'selected-row' : ''}
                    style={{ cursor: 'pointer' }}
                    onClick={() => toggleExpand(req.group_id)}
                  >
                    <td style={{ textAlign: 'center', color: 'var(--accent-orange)' }}>
                      {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </td>
                    <td>
                      <code style={{ fontWeight: 700 }}>{req.group_id}</code>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {req.pr_lines.length} Line{req.pr_lines.length > 1 ? 's' : ''}
                      </span>
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-main)' }}>{req.resolved_item_code}</strong>
                    </td>
                    <td>
                      <Badge route={req.route} size="sm" />
                    </td>
                    <td>
                      {req.supplier_id ? (
                        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                          {req.supplier_id}
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          {req.suggested_supplier_ids ? `Suggested: ${req.suggested_supplier_ids}` : 'Sourcing Event'}
                        </span>
                      )}
                    </td>
                    <td style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                      {formatINR(req.group_value_inr)}
                    </td>
                    <td>
                      <Badge
                        variant={
                          req.status === 'APPROVED' ? 'emerald' :
                          req.status === 'OVERRIDDEN' ? 'purple' : 'dim'
                        }
                        size="sm"
                      >
                        {req.status}
                      </Badge>
                    </td>
                    <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                        {req.status !== 'APPROVED' && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => onApprove(req.group_id)}
                            disabled={isLoading}
                            icon={<Check size={13} />}
                            title="Approve Recommendation"
                          >
                            Approve
                          </Button>
                        )}
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => onOpenOverride(req)}
                          disabled={isLoading}
                          icon={<Edit3 size={13} />}
                          title="Manual Route Override (Policy 8.1)"
                        >
                          Override
                        </Button>
                      </div>
                    </td>
                  </tr>

                  {/* Expandable Deep Inspection Drawer */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={9} style={{ padding: '0 1.25rem 1.25rem 1.25rem', background: '#fafafa' }}>
                        <div className="detail-card-panel">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                            <Shield size={16} color="var(--accent-orange)" />
                            <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>
                              Group Inspection & Audit Evidence: {req.group_id}
                            </strong>
                          </div>

                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', fontSize: '0.825rem' }}>
                            {/* PR Lines Breakdown */}
                            <div style={{ background: '#ffffff', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                <FileText size={14} color="var(--accent-orange)" />
                                <span>Consolidated PR Lines ({req.pr_lines.length}):</span>
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                                {req.pr_lines.map((p, idx) => (
                                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0', borderBottom: '1px dashed #f4f4f5' }}>
                                    <code>{p.pr_no} / Line {p.pr_line}</code>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Processed</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Deterministic Policy Justification */}
                            <div style={{ background: '#ffffff', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                <Info size={14} color="var(--accent-orange)" />
                                <span>Policy Decision Rationale (v{req.policy_version}):</span>
                              </div>
                              <p style={{ color: 'var(--text-muted)', lineHeight: '1.45', margin: 0 }}>
                                {req.reason}
                              </p>
                              {req.po_id && (
                                <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #f4f4f5' }}>
                                  <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Consolidated PO ID:</span>{' '}
                                  <strong style={{ color: 'var(--accent-orange)' }}>{req.po_id}</strong>
                                </div>
                              )}
                            </div>

                            {/* Recorded Audit Trail */}
                            <div style={{ background: '#ffffff', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                <Clock size={14} color="var(--accent-orange)" />
                                <span>Audit & Compliance Log:</span>
                              </div>
                              {req.audit_trail && req.audit_trail.length > 0 ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                  {req.audit_trail.map((entry, idx) => (
                                    <div key={idx} style={{ fontSize: '0.75rem', lineHeight: '1.3' }}>
                                      <span style={{ color: 'var(--text-dim)' }}>{entry.timestamp.split('T')[0]}:</span>{' '}
                                      <strong>{entry.action}</strong> by {entry.actor} ({entry.details})
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                                  Automated engine evaluation compliant with Policy v{req.policy_version}.
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <Pagination
        currentPage={currentPage}
        totalItems={sortedRequirements.length}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
};
