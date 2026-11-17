import React, { useState } from 'react';
import { ShieldAlert, AlertCircle } from 'lucide-react';
import { RequirementDecision, RouteType } from '../../types';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';

interface OverrideModalProps {
  requirement: RequirementDecision | null;
  onClose: () => void;
  onSubmit: (groupId: string, route: RouteType | string, comment: string, buyerName: string) => Promise<void>;
  isLoading: boolean;
}

export const OverrideModal: React.FC<OverrideModalProps> = ({
  requirement,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [overrideRoute, setOverrideRoute] = useState<RouteType>('SPOT_PO');
  const [overrideComment, setOverrideComment] = useState('');
  const [buyerName, setBuyerName] = useState('Lead Buyer (Corvo)');
  const [errorText, setErrorText] = useState('');

  if (!requirement) return null;

  const handleSubmit = async () => {
    if (!overrideComment.trim()) {
      setErrorText('A written justification is mandatory under Policy 8.1.');
      return;
    }

    setErrorText('');
    await onSubmit(requirement.group_id, overrideRoute, overrideComment.trim(), buyerName);
  };

  return (
    <Modal
      isOpen={!!requirement}
      onClose={onClose}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={20} color="var(--accent-amber)" />
          <span>Override Requirement {requirement.group_id}</span>
        </div>
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={isLoading}>
            Submit Formal Override
          </Button>
        </>
      }
    >
      <div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.4' }}>
          <strong>Policy Clause 8.1</strong> authorizes Lead Buyers to manually override automated routing with mandatory recorded justification.
        </p>

        <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
          <div><strong>Item Code:</strong> {requirement.resolved_item_code}</div>
          <div style={{ marginTop: '0.25rem' }}>
            <strong>System Decided Route:</strong> <code style={{ color: 'var(--accent-cyan)' }}>{requirement.route}</code>
          </div>
          <div style={{ marginTop: '0.25rem' }}>
            <strong>Requirement Value:</strong> ₹{requirement.group_value_inr.toLocaleString()}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
            Target Route:
          </label>
          <select
            className="chat-input"
            style={{ width: '100%' }}
            value={overrideRoute}
            onChange={(e) => setOverrideRoute(e.target.value as RouteType)}
          >
            <option value="SPOT_PO">SPOT PO</option>
            <option value="CONTRACT_PO">CONTRACT PO</option>
            <option value="EMERGENCY_PO">EMERGENCY PO</option>
            <option value="RFQ">RFQ SOURCING</option>
            <option value="RFP">RFP SOURCING</option>
            <option value="CAPEX_SOURCING">CAPEX SOURCING</option>
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
            Authorizing Buyer:
          </label>
          <input
            type="text"
            className="chat-input"
            style={{ width: '100%' }}
            value={buyerName}
            onChange={(e) => setBuyerName(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
            Written Justification (Audit Log Record):
          </label>
          <textarea
            className="chat-input"
            style={{ width: '100%', height: '80px', resize: 'vertical' }}
            placeholder="e.g. Critical plant maintenance requirement approved by Operations VP..."
            value={overrideComment}
            onChange={(e) => {
              setOverrideComment(e.target.value);
              if (errorText) setErrorText('');
            }}
          />
          {errorText && (
            <div style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertCircle size={12} /> {errorText}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};
