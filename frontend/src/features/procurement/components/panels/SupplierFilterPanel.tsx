import React from 'react';
import { Calendar, Download, Search, RefreshCw } from 'lucide-react';
import { Button } from '../../../../components/common/Button';

interface SupplierFilterPanelProps {
  targetDate: string;
  onTargetDateChange: (date: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  exportUrl: string;
  onRefresh: () => void;
  isLoading: boolean;
}

export const SupplierFilterPanel: React.FC<SupplierFilterPanelProps> = ({
  targetDate,
  onTargetDateChange,
  searchQuery,
  onSearchChange,
  exportUrl,
  onRefresh,
  isLoading,
}) => {
  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', margin: '0.5rem 0 1.25rem 0', flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', maxWidth: '320px', width: '100%' }}>
        <input
          type="text"
          placeholder="Search Item Code or Supplier..."
          className="chat-input"
          style={{ width: '100%', paddingLeft: '2.25rem' }}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <Search
          size={15}
          style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }}
        />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <Calendar size={15} color="var(--text-dim)" />
        <input
          type="date"
          className="chat-input"
          value={targetDate}
          onChange={(e) => onTargetDateChange(e.target.value)}
          style={{ padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
        />
      </div>

      <Button
        variant="secondary"
        size="sm"
        onClick={onRefresh}
        isLoading={isLoading}
        icon={<RefreshCw size={14} />}
      >
        Refresh Rankings
      </Button>

      <a
        href={exportUrl}
        download="preferred_suppliers.csv"
        className="btn btn-success btn-sm"
        style={{ marginLeft: 'auto', textDecoration: 'none' }}
      >
        <Download size={14} />
        <span>Export CSV</span>
      </a>
    </div>
  );
};
