import React from 'react';
import { Check, Edit3 } from 'lucide-react';
import { RequirementDecision } from '../../../../types';
import { Badge } from '../../../../components/common/Badge';
import { Button } from '../../../../components/common/Button';
import { formatINR } from '../../lib/formatters';

interface RequirementsTablePanelProps {
  requirements: RequirementDecision[];
  onApprove: (groupId: string) => void;
  onOpenOverride: (req: RequirementDecision) => void;
  isLoading: boolean;
}

export const RequirementsTablePanel: React.FC<RequirementsTablePanelProps> = ({
  requirements,
  onApprove,
  onOpenOverride,
  isLoading,
}) => {
  if (requirements.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-dim)', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-color)' }}>
        No requirements match the selected criteria.
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Group ID</th>
            <th>PR Lines</th>
            <th>Item</th>
            <th>Route</th>
            <th>Assigned / Suggested Supplier</th>
            <th>Value (INR)</th>
            <th>Policy Reason</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req) => (
            <tr key={req.group_id}>
              <td>
                <code style={{ fontWeight: 600 }}>{req.group_id}</code>
              </td>
              <td>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {req.pr_lines.map((p) => `${p.pr_no}/${p.pr_line}`).join(', ')}
                </span>
              </td>
              <td>
                <strong>{req.resolved_item_code}</strong>
              </td>
              <td>
                <Badge route={req.route} size="sm" />
              </td>
              <td>
                {req.supplier_id ? (
                  <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{req.supplier_id}</span>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {req.suggested_supplier_ids ? `Suggested: ${req.suggested_supplier_ids}` : 'None'}
                  </span>
                )}
              </td>
              <td style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                {formatINR(req.group_value_inr)}
              </td>
              <td style={{ maxWidth: '280px', fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                {req.reason}
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
              <td>
                <div style={{ display: 'flex', gap: '0.35rem' }}>
                  {req.status !== 'APPROVED' && (
                    <Button
                      variant="outline"
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
          ))}
        </tbody>
      </table>
    </div>
  );
};
