import React from 'react';
import { Building2, ShieldCheck, Activity } from 'lucide-react';
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
          <div className="brand-subtitle">PR-to-PO Decision Engine • Policy v5.0</div>
        </div>
      </div>

      <div className="header-badges">
        <span className="badge badge-blue" title="Active Policy Version">
          <ShieldCheck size={14} />
          {isLoadingPolicy ? 'Loading...' : `Policy: v${activePolicyVersion}`}
        </span>
        <span className="badge badge-dim" title="Operational Plants">
          <Building2 size={14} /> PUN1 & CHK1
        </span>
        <span className="badge badge-emerald" title="Engine Status">
          <Activity size={14} /> Online
        </span>
      </div>
    </header>
  );
};
