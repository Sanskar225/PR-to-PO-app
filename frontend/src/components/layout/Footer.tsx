import React from 'react';
import { Terminal, Shield, GitBranch } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Footer: React.FC = () => {
  const { activePolicyVersion } = useApp();

  return (
    <footer style={{
      marginTop: 'auto',
      padding: '1.5rem 2rem',
      borderTop: '1px solid var(--border-color)',
      background: 'var(--bg-secondary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem',
      fontSize: '0.8rem',
      color: 'var(--text-dim)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Shield size={14} color="var(--accent-cyan)" />
          <strong>Corvo Engineering Procurement</strong> (Policy v{activePolicyVersion})
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <GitBranch size={14} /> Clean Architecture & DDD
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <a 
          href="/api/health" 
          target="_blank" 
          rel="noreferrer"
          style={{ color: 'var(--text-muted)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
        >
          <Terminal size={13} /> Health API
        </a>
        <a 
          href="/docs" 
          target="_blank" 
          rel="noreferrer"
          style={{ color: 'var(--text-muted)', textDecoration: 'none' }}
        >
          FastAPI Swagger Docs
        </a>
        <span>Cantill.ai Round 1 Submission</span>
      </div>
    </footer>
  );
};
