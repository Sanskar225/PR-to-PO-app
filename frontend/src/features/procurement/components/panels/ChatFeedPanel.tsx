import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../../../../types';

interface ChatFeedPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export const ChatFeedPanel: React.FC<ChatFeedPanelProps> = ({ messages, isLoading }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
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
      <div ref={endRef} />
    </div>
  );
};
