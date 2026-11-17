import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '../services';
import { ChatMessage, ParsedPR } from '../../../types';
import { useToast } from '../../../context/ToastContext';

export function useChat() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome to the **Corvo Engineering Procurement Assistant**.\n\nI parse natural language requests, resolve item codes from master data, detect missing attributes, and classify procurement routes under **Policy v5.0**.\n\nTry typing a requirement or use the quick examples below.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [currentParsedPR, setCurrentParsedPR] = useState<ParsedPR | null>(null);

  const sendMessageMutation = useMutation({
    mutationFn: async (text: string) => {
      const userMessage: ChatMessage = {
        id: Math.random().toString(),
        role: 'user',
        content: text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, userMessage]);
      return chatService.sendMessage(text, currentParsedPR);
    },
    onSuccess: (response) => {
      const assistantMessage: ChatMessage = {
        id: Math.random().toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        parsed_pr: response.parsed_pr,
      };
      setMessages(prev => [...prev, assistantMessage]);
      if (response.parsed_pr) {
        setCurrentParsedPR(response.parsed_pr);
      }
    },
    onError: (err: any) => {
      error(err.message || 'Chat service failed', 'Connection Error');
      setMessages(prev => [
        ...prev,
        {
          id: Math.random().toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an issue connecting to the procurement engine. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    },
  });

  const submitPRMutation = useMutation({
    mutationFn: async () => {
      if (!currentParsedPR) throw new Error('No parsed PR to submit');
      return chatService.submitPR(currentParsedPR);
    },
    onSuccess: (result) => {
      success(
        `PR ${result.pr.pr_no} created and routed to ${result.decision.route} (${result.decision.decision})`,
        'PR Submitted Successfully'
      );
      setMessages(prev => [
        ...prev,
        {
          id: Math.random().toString(),
          role: 'assistant',
          content: `🎉 **Purchase Requisition Confirmed!**\n\n- **PR Number:** \`${result.pr.pr_no}\`\n- **Requirement Group:** \`${result.decision.group_id}\`\n- **Route:** \`${result.decision.route}\`\n- **Decision:** **${result.decision.decision}**\n- **Estimated Value:** ₹${result.decision.group_value_inr.toLocaleString()}\n- **Reason:** ${result.decision.reason}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setCurrentParsedPR(null);
      queryClient.invalidateQueries({ queryKey: ['buyer'] });
    },
    onError: (err: any) => {
      error(err.message || 'PR submission failed', 'Submission Failed');
    },
  });

  return {
    messages,
    currentParsedPR,
    setCurrentParsedPR,
    sendMessage: sendMessageMutation.mutateAsync,
    isSending: sendMessageMutation.isPending,
    submitPR: submitPRMutation.mutateAsync,
    isSubmitting: submitPRMutation.isPending,
  };
}
