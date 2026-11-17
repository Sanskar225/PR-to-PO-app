import React, { useState, useMemo } from 'react';
import { useBuyer } from '../hooks/useBuyer';
import { RequirementDecision, RouteType } from '../../../types';
import { BuyerKpiPanel, BuyerFilterBar, RequirementsTablePanel, OverrideDialog } from '../components';

export const BuyerWorkspacePage: React.FC = () => {
  const [routeFilter, setRouteFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReqForOverride, setSelectedReqForOverride] = useState<RequirementDecision | null>(null);

  const {
    requirements,
    summary,
    isLoading,
    refetch,
    approveRequirement,
    isApproving,
    overrideRequirement,
    isOverriding,
  } = useBuyer(routeFilter);

  const filteredRequirements = useMemo(() => {
    if (!searchQuery) return requirements;
    const q = searchQuery.toLowerCase();
    return requirements.filter(
      (r) =>
        r.resolved_item_code.toLowerCase().includes(q) ||
        r.group_id.toLowerCase().includes(q) ||
        (r.supplier_id && r.supplier_id.toLowerCase().includes(q))
    );
  }, [requirements, searchQuery]);

  const handleOverrideSubmit = async (
    groupId: string,
    route: RouteType | string,
    comment: string,
    buyerName: string
  ) => {
    await overrideRequirement({
      group_id: groupId,
      override_route: route,
      override_comment: comment,
      buyer_name: buyerName,
    });
    setSelectedReqForOverride(null);
  };

  return (
    <div>
      {/* 4-Card Executive KPI Panel */}
      <BuyerKpiPanel summary={summary} fallbackCount={requirements.length} />

      {/* Filter and Search Bar */}
      <BuyerFilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        routeFilter={routeFilter}
        onRouteFilterChange={setRouteFilter}
        onRefresh={() => refetch()}
        isLoading={isLoading}
      />

      {/* Requirements Table */}
      <RequirementsTablePanel
        requirements={filteredRequirements}
        onApprove={(groupId) => approveRequirement({ group_id: groupId, buyer_name: 'Lead Buyer (Corvo)' })}
        onOpenOverride={(req) => setSelectedReqForOverride(req)}
        isLoading={isApproving || isOverriding || isLoading}
      />

      {/* Policy 8.1 Override Modal Dialog */}
      <OverrideDialog
        requirement={selectedReqForOverride}
        onClose={() => setSelectedReqForOverride(null)}
        onSubmit={handleOverrideSubmit}
        isLoading={isOverriding}
      />
    </div>
  );
};
