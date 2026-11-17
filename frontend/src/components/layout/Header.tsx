import React from 'react';
import { CheckCircle2, Building2, ShieldCheck, Activity } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Header: React.FC = () => {
  const { activePolicyVersion, isLoadingPolicy } = useApp();

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo" title="Corvo Engineering">
          C
        </div>
        <div>
          <div className="brand-title">Corvo Engineering</div>
          <div className="brand-subtitle">Policy-Driven PR-to-PO Decision Engine (Clean Architecture)</div>
        </div>
      </div>

      <div className="header-badges">
        <span className="badge badge-emerald" title="Policy as Data engine version">
          <ShieldCheck size={14} />
          {isLoadingPolicy ? 'Loading...' : `Active Policy: v${activePolicyVersion}`}
        </span>
        <span className="badge badge-blue" title="Operational Manufacturing Plants">
          <Building2 size={14} /> Plants: PUN1 & CHK1
        </span>
        <span className="badge badge-dim" title="System Operational Status">
          <Activity size={14} color="#10b981" /> Engine Online
        </span>
      </div>
    </header>
  );
};
