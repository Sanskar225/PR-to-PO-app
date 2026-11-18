import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';
import { Modal } from '../../../../components/common/Modal';
import { Button } from '../../../../components/common/Button';

interface PolicyActivationDialogProps {
  isOpen: boolean;
  version: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isLoading: boolean;
}

export const PolicyActivationDialog: React.FC<PolicyActivationDialogProps> = ({
  isOpen,
  version,
  onClose,
  onConfirm,
  isLoading,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck size={20} color="var(--accent-orange)" />
          <span>Confirm Policy Activation (v{version})</span>
        </div>
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onConfirm} isLoading={isLoading}>
            Approve & Activate
          </Button>
        </>
      }
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: '#b45309' }}>
          <AlertTriangle size={24} style={{ flexShrink: 0 }} />
          <span style={{ fontSize: '0.85rem' }}>
            Activating Policy Version <strong>{version}</strong> will dynamically update all specification thresholds across live decision engines without code modification.
          </span>
        </div>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
          Are you sure you want to enforce this version for subsequent Purchase Requisitions and batch evaluations?
        </p>
      </div>
    </Modal>
  );
};
