import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { toastContainerProps } from './utils/toast.js';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <>
    <App />
    <ToastContainer {...toastContainerProps} />
  </>,
);
