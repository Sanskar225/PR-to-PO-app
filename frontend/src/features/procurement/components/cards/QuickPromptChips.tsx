import React from 'react';
import { Sparkles } from 'lucide-react';

interface QuickPromptChipsProps {
  onSelectPrompt: (text: string) => void;
}

export const QuickPromptChips: React.FC<QuickPromptChipsProps> = ({ onSelectPrompt }) => {
  const quickPrompts = [
    { label: 'Nitrile Gloves (Chakan)', text: 'need 200 nitrile gloves for Chakan by next Friday' },
    { label: 'MS Sheet 3mm (Bhosari)', text: 'need 15 nos MS sheet 3mm for Bhosari by 2026-11-15' },
    { label: 'Urgent Gearbox Oil Seal', text: 'urgent 2380 nos gearbox oil seal for Bhosari' },
    { label: 'EOT Crane 5 Ton (Capex)', text: 'need 4 nos eot crane 5 ton for Bhosari' },
  ];

  return (
    <div style={{ padding: '0 1rem 0.5rem 1rem' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <Sparkles size={12} color="var(--accent-cyan)" />
        <span>Quick Test Scenarios:</span>
      </div>
      <div className="quick-chips">
        {quickPrompts.map((q, idx) => (
          <div
            key={idx}
            className="chip"
            onClick={() => onSelectPrompt(q.text)}
          >
            {q.label}
          </div>
        ))}
      </div>
    </div>
  );
};
