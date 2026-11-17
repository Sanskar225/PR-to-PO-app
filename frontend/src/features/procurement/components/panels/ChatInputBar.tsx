import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { Button } from '../../../../components/common/Button';

interface ChatInputBarProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({ onSendMessage, isLoading }) => {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    onSendMessage(text);
    setText('');
  };

  return (
    <div className="chat-input-row">
      <input
        type="text"
        className="chat-input"
        placeholder="Type a procurement request (e.g. need 100 kg EN8 round bar for PUN1)..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        disabled={isLoading}
      />
      <Button
        variant="primary"
        onClick={handleSubmit}
        isLoading={isLoading}
        disabled={!text.trim() || isLoading}
        icon={<Send size={16} />}
      >
        Send
      </Button>
    </div>
  );
};
