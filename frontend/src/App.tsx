import React, { useState } from 'react';
import { ToastProvider } from './context/ToastContext';
import { AppProvider } from './context/AppContext';
import { Header } from './components/layout/Header';
import { Navbar, NavTabId } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { ChatView } from './features/chat/ChatView';
import { BuyerView } from './features/buyer/BuyerView';
import { BatchView } from './features/batch/BatchView';
import { PolicyView } from './features/policy/PolicyView';
import { SuppliersView } from './features/suppliers/SuppliersView';
import { ContractsView } from './features/contracts/ContractsView';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>('chat');

  return (
    <div className="app-container">
      <Header />
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content">
        {activeTab === 'chat' && <ChatView />}
        {activeTab === 'buyer' && <BuyerView />}
        {activeTab === 'batch' && <BatchView />}
        {activeTab === 'policy' && <PolicyView />}
        {activeTab === 'suppliers' && <SuppliersView />}
        {activeTab === 'contracts' && <ContractsView />}
      </main>

      <Footer />
    </div>
  );
};

export default function App() {
  return (
    <ToastProvider>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ToastProvider>
  );
}
