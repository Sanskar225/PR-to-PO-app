import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { ChatMessage, ParsedPR } from '../../types';
import { chatService } from '../../api/chatService';
import { useToast } from '../../context/ToastContext';
import { useApp } from '../../context/AppContext';
import { PRPreviewCard } from './PRPreviewCard';
import { Button } from '../../components/common/Button';

export const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome to the **Corvo Engineering Procurement Assistant**.\n\nI parse natural language requests, resolve item codes from master data, detect missing attributes, and classify procurement routes under **Policy v5.0**.\n\nTry typing a requirement or use the quick examples below.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentParsedPR, setCurrentParsedPR] = useState<ParsedPR | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { success, error, info } = useToast();
  const { triggerRefresh } = useApp();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputPrompt;
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Math.random().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputPrompt('');
    setIsLoading(true);

    try {
      const response = await chatService.sendMessage(text, currentParsedPR);
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
    } catch (err: any) {
      error(err.message || 'Failed to send message', 'Chat Error');
      setMessages(prev => [
        ...prev,
        {
          id: Math.random().toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an issue connecting to the procurement engine. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmPR = async () => {
    if (!currentParsedPR) return;
    setIsLoading(true);

    try {
      const result = await chatService.submitPR(currentParsedPR);
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
      triggerRefresh();
    } catch (err: any) {
      error(err.message || 'Failed to submit PR to engine', 'Submission Failed');
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    { label: 'Nitrile Gloves (Chakan)', text: 'need 200 nitrile gloves for Chakan by next Friday' },
    { label: 'MS Sheet 3mm (Bhosari)', text: 'need 15 nos MS sheet 3mm for Bhosari by 2026-11-15' },
    { label: 'Urgent Gearbox Oil Seal', text: 'urgent 2380 nos gearbox oil seal for Bhosari' },
    { label: 'EOT Crane 5 Ton (Capex)', text: 'need 4 nos eot crane 5 ton for Bhosari' },
  ];

  return (
    <div className="chat-layout">
      {/* Left Chat Stream */}
      <div className="chat-box">
        <div className="chat-messages">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`chat-bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}
            >
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{m.content}</div>
              <div style={{ fontSize: '0.65rem', opacity: 0.6, marginTop: '4px', textAlign: 'right' }}>
                {m.timestamp}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-bubble bubble-assistant" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
              Analyzing requirement against Procurement Policy v5.0...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Example Chips */}
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
                onClick={() => handleSendMessage(q.text)}
              >
                {q.label}
              </div>
            ))}
          </div>
        </div>

        {/* Message Input Row */}
        <div className="chat-input-row">
          <input
            type="text"
            className="chat-input"
            placeholder="Type a procurement request (e.g. need 100 kg EN8 round bar for PUN1)..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={isLoading}
          />
          <Button
            variant="primary"
            onClick={() => handleSendMessage()}
            isLoading={isLoading}
            icon={<Send size={16} />}
          >
            Send
          </Button>
        </div>
      </div>

      {/* Right Live PR Preview Card */}
      <div>
        <PRPreviewCard
          parsedPR={currentParsedPR}
          onConfirm={handleConfirmPR}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
