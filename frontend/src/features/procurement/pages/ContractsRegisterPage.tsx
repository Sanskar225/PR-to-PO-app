import React from 'react';
import { FileText, RefreshCw } from 'lucide-react';
import { useContracts } from '../hooks/useContracts';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { ContractsTablePanel } from '../components';

export const ContractsRegisterPage: React.FC = () => {
  const { contracts, isLoading, refetch } = useContracts();

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={20} color="var(--accent-cyan)" />
            <span>Active Rate Contracts & Ceiling Headroom (Policy Section 4)</span>
          </div>
        }
        subtitle="Monitors contract validity windows, cumulative consumption against value ceilings, and newly executed PDF contracts."
        action={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            isLoading={isLoading}
            icon={<RefreshCw size={14} />}
          >
            Refresh
          </Button>
        }
      >
        <ContractsTablePanel contracts={contracts} />
      </Card>
    </div>
  );
};
