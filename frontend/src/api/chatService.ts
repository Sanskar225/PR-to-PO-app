import { request } from './client';
import { ParsedPR } from '../types';

export interface ChatRequestPayload {
  role: 'user';
  content: string;
  metadata?: any;
}

export interface ChatResponsePayload {
  reply: string;
  parsed_pr: ParsedPR;
  is_complete: boolean;
}

export interface SubmitPRResponse {
  status: string;
  pr: {
    pr_no: string;
    item_code: string;
    plant: string;
    quantity: number;
    uom: string;
    need_by_date: string;
    urgency: string;
  };
  decision: {
    group_id: string;
    decision: 'DIRECT_PO' | 'SOURCING_REQUIRED';
    route: string;
    group_value_inr: number;
    supplier_id?: string;
    unit_price?: number;
    reason: string;
  };
}

export const chatService = {
  sendMessage: (content: string, metadata?: any): Promise<ChatResponsePayload> => {
    return request<ChatResponsePayload>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ role: 'user', content, metadata }),
    });
  },

  submitPR: (parsedPR: ParsedPR): Promise<SubmitPRResponse> => {
    return request<SubmitPRResponse>('/api/pr/submit', {
      method: 'POST',
      body: JSON.stringify(parsedPR),
    });
  },
};
