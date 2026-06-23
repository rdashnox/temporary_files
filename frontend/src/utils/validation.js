export const isBlank = (value) => value === null || value === undefined || String(value).trim() === '';

export const safeTrim = (value) => (value === null || value === undefined ? '' : String(value).trim());

export const isValidEmail = (value) => /^\S+@\S+\.\S+$/.test(safeTrim(value));

export const validatePasswordStrength = (password) => {
  const value = String(password || '');
  const missing = [];
  if (value.length < 8) missing.push('at least 8 characters');
  if (!/[a-z]/.test(value)) missing.push('one lowercase letter');
  if (!/[A-Z]/.test(value)) missing.push('one uppercase letter');
  if (!/\d/.test(value)) missing.push('one number');
  if (!/[^A-Za-z0-9]/.test(value)) missing.push('one special character');
  return missing;
};

export const validationError = (messages) => {
  const list = Array.isArray(messages) ? messages : [messages];
  const error = new Error(list.filter(Boolean).join(' '));
  error.name = 'ValidationError';
  error.isValidationError = true;
  return error;
};

export const requireText = (value, label, { minLength = 1, maxLength = null } = {}) => {
  const cleaned = safeTrim(value);
  if (!cleaned) throw validationError(`${label} is required.`);
  if (cleaned.length < minLength) throw validationError(`${label} must be at least ${minLength} characters.`);
  if (maxLength && cleaned.length > maxLength) throw validationError(`${label} must be at most ${maxLength} characters.`);
  return cleaned;
};

export const requireEmail = (value, label = 'Email') => {
  const email = requireText(value, label);
  if (!isValidEmail(email)) throw validationError(`${label} must be a valid email address.`);
  return email;
};

export const requireNumber = (value, label, { min = null, max = null } = {}) => {
  if (value === null || value === undefined || value === '') throw validationError(`${label} is required.`);
  const number = Number(value);
  if (!Number.isFinite(number)) throw validationError(`${label} must be a valid number.`);
  if (min !== null && number < min) throw validationError(`${label} must be at least ${min}.`);
  if (max !== null && number > max) throw validationError(`${label} must be at most ${max}.`);
  return number;
};

export const validateOrderItems = (items) => {
  if (!Array.isArray(items) || items.length === 0) {
    throw validationError('Order items must contain at least one item.');
  }

  const seen = new Set();
  return items.map((item, index) => {
    const label = `Order item #${index + 1}`;
    const productId = requireNumber(item?.product_id, `${label} product_id`, { min: 1 });
    if (seen.has(productId)) throw validationError(`Duplicate product_id ${productId} is not allowed in one order.`);
    seen.add(productId);
    return {
      product_id: productId,
      product_name: requireText(item?.product_name || item?.name, `${label} product name`, { minLength: 2, maxLength: 120 }),
      quantity: requireNumber(item?.quantity, `${label} quantity`, { min: 1, max: 999 }),
      unit_price: requireNumber(item?.unit_price, `${label} unit price`, { min: 0.01 }),
    };
  });
};
