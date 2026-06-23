import { toast } from 'react-toastify';

const DEFAULT_TOAST_OPTIONS = {
  position: 'top-center',
  autoClose: 4500,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
  theme: 'colored',
};

export const toastContainerProps = {
  position: 'top-center',
  autoClose: 4500,
  newestOnTop: true,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  limit: 4,
  theme: 'colored',
};

export const getToastMessage = (value, fallback = 'Something went wrong. Please try again.') => {
  if (!value) return fallback;
  if (typeof value === 'string') return value;
  if (value instanceof Error) return value.message || fallback;
  if (typeof value?.message === 'string') return value.message;
  if (typeof value?.detail === 'string') return value.detail;
  if (Array.isArray(value?.detail)) {
    return value.detail
      .map((item) => item?.message || item?.msg || 'Invalid value')
      .filter(Boolean)
      .join(' ');
  }
  return fallback;
};

const makeToastId = (type, message, providedId) => {
  if (providedId) return providedId;
  const normalized = String(message || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 80);
  return `finmark-${type}-${normalized || 'message'}`;
};

const notify = (type, value, options = {}) => {
  const message = getToastMessage(value, options.fallback);
  const toastId = makeToastId(type, message, options.toastId);
  const finalOptions = { ...DEFAULT_TOAST_OPTIONS, ...options, toastId };
  delete finalOptions.fallback;

  if (type === 'success') return toast.success(message, finalOptions);
  if (type === 'warning') return toast.warning(message, finalOptions);
  if (type === 'info') return toast.info(message, finalOptions);
  return toast.error(message, finalOptions);
};

export const showSuccessToast = (message, options = {}) => notify('success', message, options);
export const showErrorToast = (error, options = {}) => notify('error', error, options);
export const showWarningToast = (message, options = {}) => notify('warning', message, options);
export const showInfoToast = (message, options = {}) => notify('info', message, options);

export const showValidationToast = (error, options = {}) => showWarningToast(error, {
  fallback: 'Please check the required fields and try again.',
  ...options,
});

export const showApiErrorToast = (error, options = {}) => {
  if (error?.isValidationError || error?.status === 400 || error?.status === 422) {
    return showValidationToast(error, options);
  }
  if (error?.isAuthRequired || error?.status === 401) {
    return showErrorToast(error, { toastId: 'finmark-auth-required', ...options });
  }
  if (error?.isBackendOffline) {
    return showErrorToast(error, { toastId: 'finmark-backend-offline', ...options });
  }
  return showErrorToast(error, options);
};

export const dismissToast = (toastId) => toast.dismiss(toastId);
