import React from 'react';
import { Search, Filter, RefreshCw } from 'lucide-react';
import { Button } from '../../../../components/common/Button';

interface BuyerFilterBarProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  routeFilter: string;
  onRouteFilterChange: (val: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const BuyerFilterBar: React.FC<BuyerFilterBarProps> = ({
  searchQuery,
  onSearchChange,
  routeFilter,
  onRouteFilterChange,
  onRefresh,
  isLoading,
}) => {
  return (
    <div
      className="card"
      style={{
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}
    >
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', flex: 1 }}>
        <div style={{ position: 'relative', minWidth: '280px' }}>
          <input
            type="text"
            placeholder="Search by Item Code, Supplier, or Group..."
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={15} style={{ color: 'var(--text-dim)' }} />
          <select
            className="chat-input"
            value={routeFilter}
            onChange={(e) => onRouteFilterChange(e.target.value)}
            style={{ minWidth: '170px' }}
          >
            <option value="ALL">All Routes</option>
            <option value="CONTRACT_PO">Contract PO</option>
            <option value="SPOT_PO">Spot PO</option>
            <option value="EMERGENCY_PO">Emergency PO</option>
            <option value="RFQ">RFQ Sourcing</option>
            <option value="RFP">RFP Sourcing</option>
            <option value="CAPEX_SOURCING">Capex Sourcing</option>
          </select>
        </div>
      </div>

      <Button
        variant="secondary"
        size="sm"
        onClick={onRefresh}
        isLoading={isLoading}
        icon={<RefreshCw size={14} />}
      >
        Refresh
      </Button>
    </div>
  );
};
