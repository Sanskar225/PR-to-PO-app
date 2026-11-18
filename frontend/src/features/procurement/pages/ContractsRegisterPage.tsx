import React, { useState } from 'react';
import { FileText, RefreshCw, Upload, FileCheck } from 'lucide-react';
import { useContracts } from '../hooks/useContracts';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { ContractsTablePanel } from '../components';

export const ContractsRegisterPage: React.FC = () => {
  const { contracts, isLoading, refetch, uploadPDFContract, isUploading } = useContracts();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleUpload = async () => {
    if (!selectedFile) return;
    await uploadPDFContract(selectedFile);
    setSelectedFile(null);
  };

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={20} color="var(--accent-orange)" />
            <span>Active Rate Contracts & Ceiling Headroom (Policy Section 4)</span>
          </div>
        }
        subtitle="Monitors contract validity windows, cumulative consumption against value ceilings, and newly executed PDF contracts."
        action={
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <Badge variant="blue">
              {contracts.length} Loaded Contracts
            </Badge>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetch()}
              isLoading={isLoading}
              icon={<RefreshCw size={14} />}
            >
              Refresh
            </Button>
          </div>
        }
      >
        {/* PDF Contract Uploader (Task Section 3.8) */}
        <div
          style={{
            padding: '1rem 1.25rem',
            background: '#fafafa',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem'
          }}
        >
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)' }}>
              <FileCheck size={16} color="var(--accent-orange)" />
              <span>Ingest PDF-Only Executed Contract (Clause 4.4)</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Upload signed contract PDF (e.g. RC-2026-031 or RC-2026-033) to extract Schedule A rates into the active register.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <input
              type="file"
              accept=".pdf"
              className="chat-input"
              style={{ maxWidth: '280px', padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
              onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
              disabled={isUploading}
            />
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              isLoading={isUploading}
              icon={<Upload size={14} />}
            >
              Parse & Ingest PDF
            </Button>
          </div>
        </div>

        <ContractsTablePanel contracts={contracts} />
      </Card>
    </div>
  );
};
