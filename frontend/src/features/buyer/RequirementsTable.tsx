import React from 'react';
import { Check, Edit3 } from 'lucide-react';
import { RequirementDecision } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';

interface RequirementsTableProps {
  requirements: RequirementDecision[];
  onApprove: (groupId: string) => void;
  onOpenOverride: (req: RequirementDecision) => void;
  isLoading: boolean;
}

export const RequirementsTable: React.FC<RequirementsTableProps> = ({
  requirements,
  onApprove,
  onOpenOverride,
  isLoading,
}) => {
  if (requirements.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-dim)' }}>
        No requirements match the selected filters.
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
                <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{req.group_id}</code>
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
                  <span style={{ fontWeight: 600, color: '#fff' }}>{req.supplier_id}</span>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {req.suggested_supplier_ids ? `Suggested: ${req.suggested_supplier_ids}` : 'None'}
                  </span>
                )}
              </td>
              <td style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                ₹{req.group_value_inr.toLocaleString()}
              </td>
              <td style={{ fontSize: '0.8rem', maxWidth: '300px', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                {req.reason}
              </td>
              <td>
                <Badge 
                  variant={req.status === 'Approved' ? 'emerald' : req.status === 'Overridden' ? 'amber' : 'dim'} 
                  size="sm"
                >
                  {req.status}
                </Badge>
              </td>
              <td>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <Button
                    variant="success"
                    size="sm"
                    onClick={() => onApprove(req.group_id)}
                    title="1-Click Approve"
                    disabled={isLoading || req.status === 'Approved'}
                    icon={<Check size={12} />}
                  >
                    Approve
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onOpenOverride(req)}
                    title="Override Decision (Policy 8.1)"
                    disabled={isLoading}
                    icon={<Edit3 size={12} />}
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
