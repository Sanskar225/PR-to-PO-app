import React from 'react';
import { 
  MessageSquare, LayoutDashboard, FileSpreadsheet, ShieldAlert, 
  Award, FileText 
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export type NavTabId = 'chat' | 'buyer' | 'batch' | 'policy' | 'suppliers' | 'contracts';

interface NavbarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  const { buyerSummary } = useApp();

  const tabs: Array<{ id: NavTabId; label: string; icon: React.ReactNode; badge?: string | number }> = [
    { id: 'chat', label: 'Chat Intake', icon: <MessageSquare size={17} /> },
    { 
      id: 'buyer', 
      label: 'Buyer Workspace', 
      icon: <LayoutDashboard size={17} />,
      badge: buyerSummary?.total_requirements ? `${buyerSummary.total_requirements}` : undefined
    },
    { id: 'batch', label: 'Batch Processor', icon: <FileSpreadsheet size={17} /> },
    { id: 'policy', label: 'Policy as Data', icon: <ShieldAlert size={17} /> },
    { id: 'suppliers', label: 'Preferred Suppliers', icon: <Award size={17} /> },
    { id: 'contracts', label: 'Contracts Register', icon: <FileText size={17} /> },
  ];

  return (
    <nav className="nav-bar">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            className={`nav-tab ${isActive ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
            type="button"
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.badge && (
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: isActive ? 'var(--accent-orange)' : '#f4f4f5',
                  color: isActive ? '#ffffff' : 'var(--text-muted)',
                  fontWeight: 700,
                  marginLeft: '4px'
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
