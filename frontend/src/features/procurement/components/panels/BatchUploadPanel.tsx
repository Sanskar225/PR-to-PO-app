import React, { useState } from 'react';
import { Upload, Download } from 'lucide-react';
import { Button } from '../../../../components/common/Button';

interface BatchUploadPanelProps {
  onProcessFile: (file: File) => Promise<any> | any;
  exportUrl: string;
  isProcessing: boolean;
}

export const BatchUploadPanel: React.FC<BatchUploadPanelProps> = ({
  onProcessFile,
  exportUrl,
  isProcessing,
}) => {
  const [file, setFile] = useState<File | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    await onProcessFile(file);
  };

  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1.75rem', marginTop: '0.5rem' }}>
      <input
        type="file"
        accept=".csv"
        className="chat-input"
        style={{ maxWidth: '380px' }}
        onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
        disabled={isProcessing}
      />

      <Button
        variant="primary"
        onClick={handleUpload}
        disabled={!file || isProcessing}
        isLoading={isProcessing}
        icon={<Upload size={16} />}
      >
        Process Batch CSV
      </Button>

      <a
        href={exportUrl}
        download="decisions.csv"
        className="btn btn-success"
        style={{ marginLeft: 'auto', textDecoration: 'none' }}
      >
        <Download size={16} />
        <span>Export Decisions CSV</span>
      </a>
    </div>
  );
};
