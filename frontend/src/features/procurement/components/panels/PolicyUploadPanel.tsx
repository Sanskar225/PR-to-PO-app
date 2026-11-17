import React, { useState } from 'react';
import { FileText } from 'lucide-react';
import { Button } from '../../../../components/common/Button';

interface PolicyUploadPanelProps {
  onPreviewText: (text: string) => Promise<any> | any;
  onPreviewFile: (file: File) => Promise<any> | any;
  isLoading: boolean;
}

export const PolicyUploadPanel: React.FC<PolicyUploadPanelProps> = ({
  onPreviewText,
  onPreviewFile,
  isLoading,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');

  const handleSubmit = async () => {
    if (file) {
      await onPreviewFile(file);
    } else if (text.trim()) {
      await onPreviewText(text.trim());
    }
  };

  return (
    <div>
      <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
        Submit Policy Amendment (Blind-Test Engine)
      </h4>
      <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.4' }}>
        Upload the amendment PDF or paste the amendment notice in natural language.
      </p>

      <div style={{ marginBottom: '1.25rem' }}>
        <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
          Upload Amendment Document (.pdf / .txt):
        </label>
        <input
          type="file"
          accept=".pdf,.txt"
          className="chat-input"
          style={{ width: '100%' }}
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
          disabled={isLoading}
        />
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
          Or Enter Policy Amendment Text:
        </label>
        <textarea
          className="chat-input"
          style={{ width: '100%', height: '110px', resize: 'vertical' }}
          placeholder="e.g. Effective Date 2026-12-01. Version 5.1. Increase Spot PO threshold to INR 300,000. Increase Emergency PO limit to INR 750,000..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <Button
        variant="primary"
        onClick={handleSubmit}
        disabled={isLoading || (!file && !text.trim())}
        isLoading={isLoading}
        icon={<FileText size={16} />}
      >
        Generate Plain-English Diff
      </Button>
    </div>
  );
};
