import React from 'react';
import { useChat } from '../hooks/useChat';
import { ChatFeedPanel, ChatInputBar, QuickPromptChips, PRPreviewCard } from '../components';

export const ChatPage: React.FC = () => {
  const { messages, currentParsedPR, sendMessage, isSending, submitPR, isSubmitting } = useChat();

  return (
    <div className="chat-layout">
      {/* Left Column: Conversational Stream */}
      <div className="chat-box">
        <ChatFeedPanel messages={messages} isLoading={isSending} />
        <QuickPromptChips onSelectPrompt={(text) => sendMessage(text)} />
        <ChatInputBar onSendMessage={(text) => sendMessage(text)} isLoading={isSending} />
      </div>

      {/* Right Column: Live Structured PR Preview Card */}
      <div>
        <PRPreviewCard
          parsedPR={currentParsedPR}
          onConfirm={() => submitPR()}
          isLoading={isSubmitting}
        />
      </div>
    </div>
  );
};
