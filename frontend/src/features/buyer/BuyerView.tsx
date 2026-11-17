import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { RefreshCw, Search, Filter, Layers, CheckCircle2, ShoppingBag, DollarSign } from 'lucide-react';
import { RequirementDecision, BuyerSummary, RouteType } from '../../types';
import { buyerService } from '../../api/buyerService';
import { useToast } from '../../context/ToastContext';
import { useApp } from '../../context/AppContext';
import { StatCard } from '../../components/common/StatCard';
import { Button } from '../../components/common/Button';
import { RequirementsTable } from './RequirementsTable';
import { OverrideModal } from './OverrideModal';

export const BuyerView: React.FC = () => {
  const [requirements, setRequirements] = useState<RequirementDecision[]>([]);
  const [summary, setSummary] = useState<BuyerSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [routeFilter, setRouteFilter] = useState<string>('ALL');
  const [plantFilter, setPlantFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedReqForOverride, setSelectedReqForOverride] = useState<RequirementDecision | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const { success, error } = useToast();
  const { refreshSignal, triggerRefresh } = useApp();

  const fetchRequirements = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await buyerService.getRequirements(routeFilter, plantFilter);
      setRequirements(data.requirements || []);
      setSummary(data.summary || null);
    } catch (err: any) {
      error(err.message || 'Failed to fetch buyer requirements', 'Data Fetch Error');
    } finally {
      setIsLoading(false);
    }
  }, [routeFilter, plantFilter, error]);

  useEffect(() => {
    fetchRequirements();
  }, [fetchRequirements, refreshSignal]);

  const handleApprove = async (groupId: string) => {
    setIsActionLoading(true);
    try {
      await buyerService.approveRequirement({ group_id: groupId, buyer_name: 'Lead Buyer (Corvo)' });
      success(`Requirement ${groupId} approved and converted to purchase workflow.`, 'Requirement Approved');
      fetchRequirements();
      triggerRefresh();
    } catch (err: any) {
      error(err.message || 'Approval failed', 'Error');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleOverrideSubmit = async (
    groupId: string,
    route: RouteType | string,
    comment: string,
    buyerName: string
  ) => {
    setIsActionLoading(true);
    try {
      await buyerService.overrideRequirement({
        group_id: groupId,
        override_route: route,
        override_comment: comment,
        buyer_name: buyerName,
      });
      success(`Requirement ${groupId} re-routed to ${route} with audit justification.`, 'Decision Overridden');
      setSelectedReqForOverride(null);
      fetchRequirements();
      triggerRefresh();
    } catch (err: any) {
      error(err.message || 'Override failed', 'Error');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Client-side search filtering
  const filteredRequirements = useMemo(() => {
    return requirements.filter((r) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        r.resolved_item_code.toLowerCase().includes(q) ||
        r.group_id.toLowerCase().includes(q) ||
        (r.supplier_id && r.supplier_id.toLowerCase().includes(q))
      );
    });
  }, [requirements, searchQuery]);

  return (
    <div>
      {/* Top KPI Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <StatCard
          label="Total Requirements"
          value={summary?.total_requirements ?? requirements.length}
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
          value={`₹${(summary?.total_value ?? 0).toLocaleString()}`}
          icon={<DollarSign size={20} />}
          valueColor="var(--accent-cyan)"
          subtext="Consolidated PR valuation"
        />
      </div>

      {/* Filter and Search Bar */}
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
          <div style={{ position: 'relative', minWidth: '260px' }}>
            <input
              type="text"
              placeholder="Search by Item Code, Supplier, or Group..."
              className="chat-input"
              style={{ width: '100%', paddingLeft: '2.25rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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
              onChange={(e) => setRouteFilter(e.target.value)}
              style={{ minWidth: '160px' }}
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
          onClick={fetchRequirements}
          isLoading={isLoading}
          icon={<RefreshCw size={14} />}
        >
          Refresh
        </Button>
      </div>

      {/* Requirements Table */}
      <RequirementsTable
        requirements={filteredRequirements}
        onApprove={handleApprove}
        onOpenOverride={(req) => setSelectedReqForOverride(req)}
        isLoading={isActionLoading || isLoading}
      />

      {/* Override Modal */}
      <OverrideModal
        requirement={selectedReqForOverride}
        onClose={() => setSelectedReqForOverride(null)}
        onSubmit={handleOverrideSubmit}
        isLoading={isActionLoading}
      />
    </div>
  );
};
