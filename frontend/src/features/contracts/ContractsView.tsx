import React, { useState, useEffect, useCallback } from 'react';
import { FileText, RefreshCw, AlertCircle, FileCheck } from 'lucide-react';
import { ContractItem } from '../../types';
import { contractService } from '../../api/contractService';
import { useToast } from '../../context/ToastContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

export const ContractsView: React.FC = () => {
  const [contracts, setContracts] = useState<ContractItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const { error } = useToast();

  const fetchContracts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await contractService.getContracts();
      setContracts(data);
    } catch (err: any) {
      error(err.message || 'Failed to load contracts register', 'Contracts Error');
    } finally {
      setIsLoading(false);
    }
  }, [error]);

  useEffect(() => {
    fetchContracts();
  }, [fetchContracts]);

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
            onClick={fetchContracts}
            isLoading={isLoading}
            icon={<RefreshCw size={14} />}
          >
            Refresh
          </Button>
        }
      >
        <div className="table-wrapper" style={{ marginTop: '0.5rem' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Contract ID</th>
                <th>Supplier</th>
                <th>Validity Window</th>
                <th>Ceiling Cap (INR)</th>
                <th>Consumed Spend</th>
                <th>Remaining Headroom</th>
                <th>Contract Source</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((c) => {
                const pct = Math.min(100, Math.round((c.consumed_value / c.value_cap) * 100));
                const remaining = Math.max(0, c.value_cap - c.consumed_value);
                const isNearLimit = pct > 85;

                return (
                  <tr key={c.contract_id}>
                    <td>
                      <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{c.contract_id}</code>
                    </td>
                    <td>
                      <strong>{c.supplier_name}</strong>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>
                        ID: {c.supplier_id}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {c.start_date} → {c.end_date}
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      ₹{c.value_cap.toLocaleString()}
                    </td>
                    <td>
                      <div>
                        ₹{c.consumed_value.toLocaleString()}
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '4px' }}>
                          ({pct}%)
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <div
                          style={{
                            width: '90px',
                            height: '6px',
                            background: 'var(--bg-tertiary)',
                            borderRadius: '4px',
                            overflow: 'hidden'
                          }}
                        >
                          <div
                            style={{
                              width: `${pct}%`,
                              height: '100%',
                              background: isNearLimit ? 'var(--accent-rose)' : 'var(--accent-cyan)',
                              transition: 'width 0.3s ease'
                            }}
                          />
                        </div>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: isNearLimit ? '#fb7185' : '#f8fafc' }}>
                          ₹{remaining.toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td>
                      {c.is_pdf_extracted ? (
                        <Badge variant="purple" size="sm">
                          <FileCheck size={12} style={{ display: 'inline', marginRight: '3px' }} />
                          PDF Extracted
                        </Badge>
                      ) : (
                        <Badge variant="dim" size="sm">
                          CSV Register
                        </Badge>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
