import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { PolicyMetadata, BuyerSummary } from '../types';
import { policyService } from '../api/policyService';
import { buyerService } from '../api/buyerService';
import { useToast } from './ToastContext';

interface AppContextType {
  activePolicyVersion: string;
  currentPolicy: PolicyMetadata | null;
  buyerSummary: BuyerSummary | null;
  refreshSignal: number;
  triggerRefresh: () => void;
  refreshPolicy: () => Promise<void>;
  refreshBuyerData: () => Promise<void>;
  isLoadingPolicy: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentPolicy, setCurrentPolicy] = useState<PolicyMetadata | null>(null);
  const [activePolicyVersion, setActivePolicyVersion] = useState<string>('5.0');
  const [buyerSummary, setBuyerSummary] = useState<BuyerSummary | null>(null);
  const [refreshSignal, setRefreshSignal] = useState<number>(0);
  const [isLoadingPolicy, setIsLoadingPolicy] = useState<boolean>(true);
  const { error } = useToast();

  const triggerRefresh = useCallback(() => {
    setRefreshSignal(prev => prev + 1);
  }, []);

  const refreshPolicy = useCallback(async () => {
    try {
      setIsLoadingPolicy(true);
      const policy = await policyService.getCurrentPolicy();
      setCurrentPolicy(policy);
      setActivePolicyVersion(policy.version);
    } catch (err: any) {
      console.error('Failed to load current policy', err);
      error(err.message || 'Could not retrieve active policy version', 'Policy Service');
    } finally {
      setIsLoadingPolicy(false);
    }
  }, [error]);

  const refreshBuyerData = useCallback(async () => {
    try {
      const data = await buyerService.getRequirements();
      if (data && data.summary) {
        setBuyerSummary(data.summary);
      }
    } catch (err: any) {
      console.error('Failed to load buyer summary', err);
    }
  }, []);

  useEffect(() => {
    refreshPolicy();
    refreshBuyerData();
  }, [refreshPolicy, refreshBuyerData]);

  return (
    <AppContext.Provider
      value={{
        activePolicyVersion,
        currentPolicy,
        buyerSummary,
        refreshSignal,
        triggerRefresh,
        refreshPolicy,
        refreshBuyerData,
        isLoadingPolicy,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
