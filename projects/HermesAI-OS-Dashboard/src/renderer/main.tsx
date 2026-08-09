import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';
import { EventBusProvider } from './context/EventBusContext';
import { ConfigProvider } from './context/ConfigContext';
import './styles/globals.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider>
        <EventBusProvider>
          <App />
        </EventBusProvider>
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
);