import React, { useState } from 'react';
import { ToastProvider } from './context/ToastContext';
import { AppProvider } from './context/AppContext';
import { Header } from './components/layout/Header';
import { Navbar, NavTabId } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { 
  ChatPage, 
  BuyerWorkspacePage, 
  BatchProcessorPage, 
  PolicyManagerPage, 
  PreferredSuppliersPage, 
  ContractsRegisterPage 
} from './features/procurement/pages';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>('chat');

  return (
    <div className="app-container">
      <Header />
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content">
        {activeTab === 'chat' && <ChatPage />}
        {activeTab === 'buyer' && <BuyerWorkspacePage />}
        {activeTab === 'batch' && <BatchProcessorPage />}
        {activeTab === 'policy' && <PolicyManagerPage />}
        {activeTab === 'suppliers' && <PreferredSuppliersPage />}
        {activeTab === 'contracts' && <ContractsRegisterPage />}
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
