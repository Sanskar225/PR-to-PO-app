import React from 'react';
import { RouteType } from '../../types';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'blue' | 'emerald' | 'amber' | 'purple' | 'cyan' | 'rose' | 'dim' | 'outline';
  route?: RouteType | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant,
  route,
  size = 'md',
  className = '',
}) => {
  // If route is supplied, infer the styling and label automatically
  if (route) {
    let resolvedVariant = 'badge-dim';
    let label = route.replace(/_/g, ' ');

    switch (route) {
      case 'CONTRACT_PO':
        resolvedVariant = 'badge-blue';
        label = 'CONTRACT PO';
        break;
      case 'SPOT_PO':
        resolvedVariant = 'badge-emerald';
        label = 'SPOT PO';
        break;
      case 'EMERGENCY_PO':
        resolvedVariant = 'badge-amber';
        label = 'EMERGENCY PO';
        break;
      case 'RFQ':
        resolvedVariant = 'badge-purple';
        label = 'RFQ SOURCING';
        break;
      case 'RFP':
        resolvedVariant = 'badge-cyan';
        label = 'RFP SOURCING';
        break;
      case 'CAPEX_SOURCING':
        resolvedVariant = 'badge-rose';
        label = 'CAPEX SOURCING';
        break;
      case 'NEW_ITEM_SOURCING':
        resolvedVariant = 'badge-dim';
        label = 'NEW ITEM SOURCING';
        break;
    }

    return (
      <span className={`badge ${resolvedVariant} ${size === 'sm' ? 'text-xs py-0.5' : ''} ${className}`}>
        {children || label}
      </span>
    );
  }

  const variantClass = variant ? `badge-${variant}` : 'badge-dim';
  return (
    <span className={`badge ${variantClass} ${size === 'sm' ? 'text-xs py-0.5' : ''} ${className}`}>
      {children}
    </span>
  );
};
