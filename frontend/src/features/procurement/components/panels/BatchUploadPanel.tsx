import React, { useState, useRef } from 'react';
import { Upload, Download, FileSpreadsheet, CheckCircle2, ArrowRight } from 'lucide-react';
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
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!file) return;
    await onProcessFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
      }
    }
  };

  return (
    <div style={{ marginBottom: '1.75rem' }}>
      {/* 4-Step Pipeline Stepper */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.75rem',
          marginBottom: '1.5rem',
          padding: '1rem',
          background: '#fafafa',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'var(--accent-orange)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>1</span>
          <div>
            <strong style={{ display: 'block', color: 'var(--text-main)' }}>Ingest Requisitions</strong>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Parse multi-line PR CSV</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'var(--accent-orange)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>2</span>
          <div>
            <strong style={{ display: 'block', color: 'var(--text-main)' }}>Anti-Splitting Clubbing</strong>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Group item + plant (24h)</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'var(--accent-orange)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>3</span>
          <div>
            <strong style={{ display: 'block', color: 'var(--text-main)' }}>Policy Specification</strong>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Contract $\rightarrow$ Spot $\rightarrow$ Sourcing</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'var(--accent-orange)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>4</span>
          <div>
            <strong style={{ display: 'block', color: 'var(--text-main)' }}>Consolidate POs</strong>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Generate PO-2026-XXXX</span>
          </div>
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-orange)' : 'var(--border-color)'}`,
          background: isDragging ? 'var(--accent-orange-light)' : '#ffffff',
          borderRadius: 'var(--radius-lg)',
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          marginBottom: '1.25rem',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
          disabled={isProcessing}
        />

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
          <FileSpreadsheet size={24} />
        </div>

        {file ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', color: '#16a34a', fontWeight: 600, fontSize: '0.95rem' }}>
              <CheckCircle2 size={18} />
              <span>{file.name}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              {(file.size / 1024).toFixed(1)} KB • Ready to process
            </div>
          </div>
        ) : (
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '0.35rem' }}>
              Click to select or drag and drop a PR batch CSV file
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Supports PR batch files with columns: pr_no, pr_line, item_code, quantity, plant, need_by_date...
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <Button
          variant="primary"
          onClick={handleUpload}
          disabled={!file || isProcessing}
          isLoading={isProcessing}
          icon={<Upload size={16} />}
        >
          Execute Batch Policy Evaluation
        </Button>

        <a
          href={exportUrl}
          download="decisions.csv"
          className="btn btn-secondary"
          style={{ marginLeft: 'auto', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Download size={15} color="var(--accent-orange)" />
          <span>Export 13-Column Decisions CSV</span>
        </a>
      </div>
    </div>
  );
};
