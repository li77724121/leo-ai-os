import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import type { DashboardConfig } from '@shared/types';
import { DEFAULT_CONFIG } from '@shared/types';

interface ConfigState {
  config: DashboardConfig;
  loading: boolean;
}

type Action =
  | { type: 'SET_CONFIG'; payload: DashboardConfig }
  | { type: 'UPDATE_CONFIG'; payload: Partial<DashboardConfig> }
  | { type: 'SET_LOADING'; payload: boolean };

const initialState: ConfigState = {
  config: DEFAULT_CONFIG,
  loading: true,
};

function configReducer(state: ConfigState, action: Action): ConfigState {
  switch (action.type) {
    case 'SET_CONFIG':
      return { ...state, config: action.payload, loading: false };
    case 'UPDATE_CONFIG':
      return { ...state, config: { ...state.config, ...action.payload } };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    default:
      return state;
  }
}

const ConfigContext = createContext<{
  state: ConfigState;
  dispatch: React.Dispatch<Action>;
  updateConfig: (partial: Partial<DashboardConfig>) => Promise<void>;
} | null>(null);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(configReducer, initialState);

  // 初始化加载配置
  useEffect(() => {
    window.electron.config.get().then((config: any) => {
      dispatch({ type: 'SET_CONFIG', payload: config });
    }).catch(() => {
      dispatch({ type: 'SET_CONFIG', payload: DEFAULT_CONFIG });
    });
  }, []);

  const updateConfig = async (partial: Partial<DashboardConfig>) => {
    const newConfig = await window.electron.config.set(partial);
    dispatch({ type: 'SET_CONFIG', payload: newConfig });
  };

  return (
    <ConfigContext.Provider value={{ state, dispatch, updateConfig }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (!context) throw new Error('useConfig must be used within ConfigProvider');
  return context;
}