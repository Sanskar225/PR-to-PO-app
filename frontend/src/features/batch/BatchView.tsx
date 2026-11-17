import React, { useState } from 'react';
import { FileSpreadsheet, Upload, Download, CheckCircle2, Layers, DollarSign } from 'lucide-react';
import { BatchProcessResult } from '../../types';
import { batchService } from '../../api/batchService';
import { useToast } from '../../context/ToastContext';
import { useApp } from '../../context/AppContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

export const BatchView: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BatchProcessResult | null>(null);

  const { success, error } = useToast();
  const { triggerRefresh, activePolicyVersion } = useApp();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleProcessBatch = async () => {
    if (!selectedFile) return;
    setIsLoading(true);

    try {
      const data = await batchService.processBatch(selectedFile);
      setResult(data);
      success(
        `Batch processed: ${data.total_lines} lines grouped into ${data.unique_requirements} requirements (${data.consolidated_pos} POs) under Policy v${data.policy_version_applied}`,
        'Batch Processing Succeeded'
      );
      triggerRefresh();
    } catch (err: any) {
      error(err.message || 'Batch execution failed', 'Batch Processing Error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileSpreadsheet size={20} color="var(--accent-cyan)" />
            <span>Batch PR Processing & Blind-Test Engine</span>
          </div>
        }
        subtitle="Ingests multi-line PR CSV datasets, executes chronological clubbing, valuation cascade, and generates consolidated POs."
        action={
          <Badge variant="blue">
            Active Policy: v{activePolicyVersion}
          </Badge>
        }
      >
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1.75rem', marginTop: '0.5rem' }}>
          <input
            type="file"
            accept=".csv"
            className="chat-input"
            style={{ maxWidth: '380px' }}
            onChange={handleFileChange}
            disabled={isLoading}
          />

          <Button
            variant="primary"
            onClick={handleProcessBatch}
            disabled={!selectedFile || isLoading}
            isLoading={isLoading}
            icon={<Upload size={16} />}
          >
            Process Batch CSV
          </Button>

          <a
            href={batchService.getDecisionsExportUrl()}
            download="decisions.csv"
            className="btn btn-success"
            style={{ marginLeft: 'auto', textDecoration: 'none' }}
          >
            <Download size={16} />
            <span>Export Decisions CSV</span>
          </a>
        </div>

        {result && (
          <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
              <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>PR Lines Processed</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>{result.total_lines}</div>
              </div>

              <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Requirement Groups</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{result.unique_requirements}</div>
              </div>

              <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Consolidated POs (24h)</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{result.consolidated_pos}</div>
              </div>

              <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Total Spend (INR)</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-amber)' }}>₹{result.total_value_inr.toLocaleString()}</div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={16} color="var(--accent-cyan)" />
                <span>Route Distribution Breakdown (Policy v{result.policy_version_applied}):</span>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {Object.entries(result.route_distribution).map(([route, count]) => (
                  <div
                    key={route}
                    style={{
                      padding: '0.6rem 1rem',
                      background: 'var(--bg-primary)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-color)',
                      display: 'flex',
                      gap: '0.75rem',
                      alignItems: 'center'
                    }}
                  >
                    <Badge route={route} size="sm" />
                    <strong style={{ fontSize: '0.95rem', color: '#fff' }}>{count}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
