import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, Upload, FileText, ArrowRight, AlertTriangle } from 'lucide-react';
import { PolicyAmendmentDiff } from '../../types';
import { policyService } from '../../api/policyService';
import { useToast } from '../../context/ToastContext';
import { useApp } from '../../context/AppContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

export const PolicyView: React.FC = () => {
  const [amendmentText, setAmendmentText] = useState('');
  const [amendmentFile, setAmendmentFile] = useState<File | null>(null);
  const [diff, setDiff] = useState<PolicyAmendmentDiff | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApproving, setIsApproving] = useState(false);

  const { success, error, info } = useToast();
  const { activePolicyVersion, currentPolicy, refreshPolicy, triggerRefresh } = useApp();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setAmendmentFile(e.target.files[0]);
    }
  };

  const handlePreviewDiff = async () => {
    setIsLoading(true);
    try {
      let diffData: PolicyAmendmentDiff;
      if (amendmentFile) {
        diffData = await policyService.previewAmendmentFile(amendmentFile);
      } else if (amendmentText.trim()) {
        diffData = await policyService.previewAmendmentText(amendmentText.trim());
      } else {
        return;
      }
      setDiff(diffData);
      info(`Amendment diff generated for proposed version ${diffData.new_version}`, 'Diff Preview');
    } catch (err: any) {
      error(err.message || 'Failed to parse policy amendment', 'Parsing Error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!diff) return;
    setIsApproving(true);
    try {
      await policyService.approveAmendment(diff.new_version);
      success(
        `Policy Version ${diff.new_version} is now approved and active across all decision engines!`,
        'Policy Activated'
      );
      setDiff(null);
      setAmendmentText('');
      setAmendmentFile(null);
      await refreshPolicy();
      triggerRefresh();
    } catch (err: any) {
      error(err.message || 'Failed to activate policy amendment', 'Activation Failed');
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={20} color="var(--accent-cyan)" />
            <span>Policy as Data Engine (Version {activePolicyVersion})</span>
          </div>
        }
        subtitle="Policy rules are stored declaratively as data. Amendments compile into dynamic specification trees with zero code changes."
        action={
          <Badge variant="emerald">
            Active: v{activePolicyVersion}
          </Badge>
        }
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem', marginTop: '0.5rem' }}>
          {/* Left: Input Form */}
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
                onChange={handleFileChange}
                disabled={isLoading || isApproving}
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
                value={amendmentText}
                onChange={(e) => setAmendmentText(e.target.value)}
                disabled={isLoading || isApproving}
              />
            </div>

            <Button
              variant="primary"
              onClick={handlePreviewDiff}
              disabled={isLoading || isApproving || (!amendmentFile && !amendmentText.trim())}
              isLoading={isLoading}
              icon={<FileText size={16} />}
            >
              Generate Plain-English Diff
            </Button>
          </div>

          {/* Right: Diff & Impact Preview Pane */}
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Diff & Specification Impact Preview
            </h4>
            {diff ? (
              <div
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                  animation: 'fadeIn 0.25s ease-out'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    v{diff.base_version}
                  </span>
                  <ArrowRight size={15} color="var(--text-dim)" />
                  <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                    Proposed v{diff.new_version}
                  </span>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                  Target Effective Date: <strong>{diff.effective_date}</strong>
                </div>

                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.825rem', fontWeight: 600, marginBottom: '0.5rem', color: '#f8fafc' }}>
                    Detected Policy Clause Changes:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.825rem', color: '#34d399', lineHeight: '1.5' }}>
                    {diff.summary_of_changes.map((change, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{change}</li>
                    ))}
                  </ul>
                </div>

                <Button
                  variant="success"
                  style={{ width: '100%' }}
                  onClick={handleApprove}
                  isLoading={isApproving}
                  icon={<CheckCircle2 size={16} />}
                >
                  Approve & Activate Version {diff.new_version}
                </Button>
              </div>
            ) : (
              <div
                style={{
                  padding: '2.5rem 1.5rem',
                  textAlign: 'center',
                  color: 'var(--text-dim)',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px dashed var(--border-color)',
                  fontSize: '0.85rem'
                }}
              >
                Upload an amendment PDF or paste revision text on the left to review the computed diff and specification rules before activation.
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};
