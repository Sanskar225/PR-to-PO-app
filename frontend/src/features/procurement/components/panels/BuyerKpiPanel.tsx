import React from 'react';
import { Layers, CheckCircle2, ShoppingBag, DollarSign } from 'lucide-react';
import { BuyerSummary } from '../../../../types';
import { StatCard } from '../../../../components/common/StatCard';
import { formatCompactINR } from '../../lib/formatters';

interface BuyerKpiPanelProps {
  summary: BuyerSummary | null;
  fallbackCount: number;
}

export const BuyerKpiPanel: React.FC<BuyerKpiPanelProps> = ({ summary, fallbackCount }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
      <StatCard
        label="Total Requirements"
        value={summary?.total_requirements ?? fallbackCount}
        icon={<Layers size={20} />}
        subtext="Active grouped requisitions"
      />
      <StatCard
        label="Direct POs"
        value={summary?.total_pos ?? 0}
        icon={<CheckCircle2 size={20} />}
        valueColor="var(--accent-emerald)"
        subtext="Contract & Spot POs"
      />
      <StatCard
        label="Sourcing Events"
        value={summary?.total_sourcing ?? 0}
        icon={<ShoppingBag size={20} />}
        valueColor="var(--accent-purple)"
        subtext="RFQ, RFP, & Capex"
      />
      <StatCard
        label="Total Spend Value"
        value={formatCompactINR(summary?.total_value ?? 0)}
        icon={<DollarSign size={20} />}
        valueColor="var(--accent-cyan)"
        subtext="Consolidated PR valuation"
      />
    </div>
  );
};
