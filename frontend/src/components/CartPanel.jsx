import { useMemo, useState } from 'react';

const currency = new Intl.NumberFormat('en-PH', {
  style: 'currency',
  currency: 'PHP',
  maximumFractionDigits: 0,
});

export default function CartPanel({ cartItems, subtotal, onUpdateQuantity, onClear, onCheckout }) {
  const [checkoutForm, setCheckoutForm] = useState({
    customerName: 'Demo Customer',
    deliveryAddress: '123 FinMark Street, Manila',
    paymentMethod: 'Cash on Delivery',
    couponCode: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const estimatedDiscount = useMemo(() => {
    return checkoutForm.couponCode.trim().toUpperCase() === 'SAVE10' ? subtotal * 0.1 : 0;
  }, [checkoutForm.couponCode, subtotal]);

  const estimatedShipping = subtotal >= 3000 || subtotal === 0 ? 0 : 150;
  const estimatedTax = Math.max(subtotal - estimatedDiscount, 0) * 0.12;
  const estimatedTotal = subtotal - estimatedDiscount + estimatedShipping + estimatedTax;

  const handleChange = (event) => {
    const { name, value } = event.target;
    setCheckoutForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!cartItems.length) {
      setError('Please add at least one product before checkout.');
      return;
    }

    setLoading(true);
    try {
      await onCheckout(checkoutForm);
      setCheckoutForm((current) => ({ ...current, couponCode: '' }));
    } catch (err) {
      setError(err.message || 'Checkout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="cart-panel glass-card" id="checkout">
      <div className="cart-header">
        <div>
          <p className="eyebrow">Checkout cart</p>
          <h2>Order Summary</h2>
        </div>
        <button className="text-btn" type="button" onClick={onClear} disabled={!cartItems.length}>Clear</button>
      </div>

      <div className="cart-list">
        {!cartItems.length && (
          <div className="empty-cart">
            <span>🛒</span>
            <p>Your cart is empty. Add products to start checkout.</p>
          </div>
        )}

        {cartItems.map((item) => (
          <div className="cart-item" key={item.id}>
            <div className="cart-item-icon">{item.image}</div>
            <div className="cart-item-content">
              <strong>{item.name}</strong>
              <span>{currency.format(item.price)} each</span>
              <div className="quantity-controls">
                <button type="button" onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}>-</button>
                <strong>{item.quantity}</strong>
                <button type="button" onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}>+</button>
              </div>
            </div>
            <strong className="line-total">{currency.format(item.price * item.quantity)}</strong>
          </div>
        ))}
      </div>

      <div className="totals-box">
        <div><span>Subtotal</span><strong>{currency.format(subtotal)}</strong></div>
        <div><span>Discount</span><strong>-{currency.format(estimatedDiscount)}</strong></div>
        <div><span>Shipping</span><strong>{estimatedShipping ? currency.format(estimatedShipping) : 'Free'}</strong></div>
        <div><span>VAT estimate</span><strong>{currency.format(estimatedTax)}</strong></div>
        <div className="grand-total"><span>Total</span><strong>{currency.format(estimatedTotal)}</strong></div>
      </div>

      <form className="checkout-form" onSubmit={handleSubmit}>
        <label>
          Customer Name
          <input name="customerName" value={checkoutForm.customerName} onChange={handleChange} required />
        </label>
        <label>
          Delivery Address
          <textarea name="deliveryAddress" value={checkoutForm.deliveryAddress} onChange={handleChange} required />
        </label>
        <label>
          Payment Method
          <select name="paymentMethod" value={checkoutForm.paymentMethod} onChange={handleChange}>
            <option>Cash on Delivery</option>
            <option>Bank Transfer</option>
            <option>GCash</option>
          </select>
        </label>
        <label>
          Coupon Code
          <input name="couponCode" value={checkoutForm.couponCode} onChange={handleChange} placeholder="Try SAVE10" />
        </label>

        {error && <div className="alert error">{error}</div>}

        <button className="primary-btn full" type="submit" disabled={loading || !cartItems.length}>
          {loading ? 'Processing...' : 'Checkout now'}
        </button>
      </form>
    </section>
  );
}
