/**
 * Frontend Domain Type Definitions
 * Corvo Engineering - PR-to-PO Decision Engine
 */

export type RouteType = 
  | 'CONTRACT_PO'
  | 'SPOT_PO'
  | 'EMERGENCY_PO'
  | 'RFQ'
  | 'RFP'
  | 'CAPEX_SOURCING'
  | 'NEW_ITEM_SOURCING';

export type PlantCode = 'PUN1' | 'CHK1';

export type UrgencyLevel = 'Normal' | 'Emergency';

export interface PRLineSummary {
  pr_no: string;
  pr_line: number;
}

export interface ParsedPR {
  item_code?: string;
  description?: string;
  quantity?: number;
  uom?: string;
  plant?: PlantCode | string;
  need_by_date?: string;
  urgency?: UrgencyLevel | string;
  estimated_unit_price?: number;
  missing_fields: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  parsed_pr?: ParsedPR;
}

export interface RequirementDecision {
  group_id: string;
  resolved_item_code: string;
  decision: 'DIRECT_PO' | 'SOURCING_REQUIRED';
  route: RouteType;
  po_id?: string;
  supplier_id?: string;
  unit_price?: number;
  group_value_inr: number;
  suggested_supplier_ids?: string;
  policy_version: string;
  reason: string;
  status: string;
  pr_lines: PRLineSummary[];
  audit_trail: Array<{
    timestamp: string;
    action: string;
    actor: string;
    details: string;
  }>;
}

export interface BuyerSummary {
  total_requirements: number;
  total_pos: number;
  total_sourcing: number;
  total_value: number;
  route_breakdown: Record<string, number>;
}

export interface BuyerWorkspaceData {
  summary: BuyerSummary;
  requirements: RequirementDecision[];
}

export interface ContractItem {
  contract_id: string;
  supplier_id: string;
  supplier_name: string;
  start_date: string;
  end_date: string;
  value_cap: number;
  consumed_value: number;
  is_pdf_extracted: boolean;
  rates?: Record<string, number>;
}

export interface RankedSupplier {
  rank: number;
  supplier_id: string;
  supplier_name: string;
  reference_price: number;
  composite_score: number;
  po_count_548d: number;
  recency_score: number;
  has_contract: boolean;
  on_time_pct: number;
  quality_rating: number;
}

export interface PreferredSuppliersResponse {
  date: string;
  total_items: number;
  items: Record<string, RankedSupplier[]>;
}

export interface BatchProcessResult {
  batch_id: string;
  total_lines: number;
  unique_requirements: number;
  consolidated_pos: number;
  total_value_inr: number;
  route_distribution: Record<string, number>;
  policy_version_applied: string;
  generated_at: string;
}

export interface PolicyMetadata {
  version: string;
  policy_id: string;
  name: string;
  effective_date: string;
  owner: string;
  is_active: boolean;
  rules_json?: any;
}

export interface PolicyAmendmentDiff {
  base_version: string;
  new_version: string;
  effective_date: string;
  summary_of_changes: string[];
  proposed_rules: any[];
}
