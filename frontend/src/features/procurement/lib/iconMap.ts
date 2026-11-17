import React from 'react';
import { 
  FileText, CheckCircle2, AlertTriangle, AlertCircle, ShoppingBag, 
  Layers, DollarSign, Clock, ShieldCheck, Award, FileSpreadsheet, 
  Send, RefreshCw, Upload, Download, Search, Filter, Edit3, X,
  Building2, Activity, Sparkles, FileCheck, ArrowRight
} from 'lucide-react';
import { RouteType } from '../../../types';

export const iconMap = {
  file: FileText,
  check: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  bag: ShoppingBag,
  layers: Layers,
  dollar: DollarSign,
  clock: Clock,
  shield: ShieldCheck,
  award: Award,
  spreadsheet: FileSpreadsheet,
  send: Send,
  refresh: RefreshCw,
  upload: Upload,
  download: Download,
  search: Search,
  filter: Filter,
  edit: Edit3,
  close: X,
  building: Building2,
  activity: Activity,
  sparkles: Sparkles,
  fileCheck: FileCheck,
  arrowRight: ArrowRight,
};

export function getRouteBadgeVariant(route: RouteType | string): 'blue' | 'emerald' | 'amber' | 'purple' | 'cyan' | 'rose' | 'dim' {
  switch (route) {
    case 'CONTRACT_PO':
      return 'blue';
    case 'SPOT_PO':
      return 'emerald';
    case 'EMERGENCY_PO':
      return 'amber';
    case 'RFQ':
      return 'purple';
    case 'RFP':
      return 'cyan';
    case 'CAPEX_SOURCING':
      return 'rose';
    default:
      return 'dim';
  }
}
