import { AsyncLocalStorage } from 'node:async_hooks';
import axios from 'axios';

export const tracing = new AsyncLocalStorage<{
  correlationId: string;
  operationId: string;
}>();

axios.interceptors.request.use((config) => {
  const context = tracing.getStore();
  if (context) {
    config.headers.set('X-Correlation-ID', context.correlationId);
    config.headers.set('X-Operation-ID', context.operationId);
  }
  if (!config.timeout) config.timeout = 8000;
  return config;
});
