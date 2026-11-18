import React, { useState, useMemo } from 'react';
import { Award } from 'lucide-react';
import { useSuppliers } from '../hooks/useSuppliers';
import { Card } from '../../../components/common/Card';
import { SupplierFilterPanel, SupplierRankingTablePanel } from '../components';

export const PreferredSuppliersPage: React.FC = () => {
  const [targetDate, setTargetDate] = useState('2026-11-01');
  const [searchQuery, setSearchQuery] = useState('');

  const { items, isLoading, refetch, exportUrl } = useSuppliers(targetDate);

  const filteredEntries = useMemo(() => {
    const entries = Object.entries(items);
    if (!searchQuery) return entries;

    const q = searchQuery.toLowerCase();
    return entries.filter(([itemCode, suppliers]) => {
      if (itemCode.toLowerCase().includes(q)) return true;
      return suppliers.some(
        s => s.supplier_name.toLowerCase().includes(q) || s.supplier_id.toLowerCase().includes(q)
      );
    });
  }, [items, searchQuery]);

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={20} color="var(--accent-orange)" />
            <span>Preferred Supplier Directory (Policy Section 6)</span>
          </div>
        }
        subtitle="Analytical multi-criteria ranking model evaluating 548-day order history, recency, active contracts, on-time delivery, and quality."
      >
        <SupplierFilterPanel
          targetDate={targetDate}
          onTargetDateChange={setTargetDate}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          exportUrl={exportUrl}
          onRefresh={() => refetch()}
          isLoading={isLoading}
        />

        <SupplierRankingTablePanel entries={filteredEntries} isLoading={isLoading} />
      </Card>
    </div>
  );
};
