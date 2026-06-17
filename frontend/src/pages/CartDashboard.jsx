import { useEffect, useMemo, useState } from 'react';
import { checkoutCart, getProducts } from '../api/client.js';
import CartPanel from '../components/CartPanel.jsx';
import ProductCard from '../components/ProductCard.jsx';
import StatCard from '../components/StatCard.jsx';
import { getDisplayName, getRoleNames, normalizeUser } from '../utils/access.js';

const currency = new Intl.NumberFormat('en-PH', {
  style: 'currency',
  currency: 'PHP',
  maximumFractionDigits: 0,
});

const baseNavSections = [
  { icon: '⌂', label: 'Dashboard', target: 'dashboard' },
  { icon: '▣', label: 'Inventory', target: 'inventory' },
  { icon: '◫', label: 'Orders', target: 'orders' },
  { icon: '⇄', label: 'Shipments', target: 'shipments' },
  { icon: '🛒', label: 'Storefront', target: 'storefront', active: true },
  { icon: '◴', label: 'Reports', target: 'reports' },
  { icon: '?', label: 'Support', target: 'support' },
];

const categoryShortcuts = ['All', 'Finance Tools', 'Marketing', 'Operations', 'Analytics', 'E-Commerce', 'Support'];

export default function CartDashboard({ user: rawUser, onLogout, onOpenAdmin, canOpenAdmin = false }) {
  const user = useMemo(() => normalizeUser(rawUser), [rawUser]);
  const displayName = getDisplayName(user);
  const roleNames = getRoleNames(user);
  const roleLabel = roleNames.length ? roleNames.map((role) => role.charAt(0).toUpperCase() + role.slice(1)).join(', ') : 'Product user';
  const navSections = useMemo(() => (
    canOpenAdmin
      ? [...baseNavSections, { icon: '🛡️', label: 'Admin CRUD', target: 'admin-crud', admin: true }]
      : baseNavSections
  ), [canOpenAdmin]);

  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({});
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [order, setOrder] = useState(null);

  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getProducts();
        setProducts(data);
      } catch (err) {
        setError(err.message || 'Unable to load products.');
      } finally {
        setLoading(false);
      }
    };

    loadProducts();
  }, []);

  const cartItems = useMemo(() => {
    return Object.entries(cart)
      .map(([productId, quantity]) => {
        const product = products.find((item) => item.id === Number(productId));
        return product ? { ...product, quantity } : null;
      })
      .filter(Boolean);
  }, [cart, products]);

  const availableCategories = useMemo(() => {
    const backendCategories = Array.from(new Set(products.map((product) => product.category)));
    const merged = ['All', ...categoryShortcuts.filter((item) => item !== 'All'), ...backendCategories];
    return Array.from(new Set(merged));
  }, [products]);

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return products.filter((product) => {
      const matchesCategory = category === 'All' || product.category === category;
      const matchesSearch =
        !normalizedQuery ||
        product.name.toLowerCase().includes(normalizedQuery) ||
        product.category.toLowerCase().includes(normalizedQuery) ||
        product.description.toLowerCase().includes(normalizedQuery);
      return matchesCategory && matchesSearch;
    });
  }, [category, products, query]);

  const subtotal = useMemo(
    () => cartItems.reduce((total, item) => total + item.price * item.quantity, 0),
    [cartItems],
  );

  const cartCount = useMemo(
    () => cartItems.reduce((total, item) => total + item.quantity, 0),
    [cartItems],
  );

  const lowStockProducts = useMemo(
    () => products.filter((product) => product.stock <= 12),
    [products],
  );

  const cartEfficiency = useMemo(() => {
    if (!products.length) return 0;
    return Math.min(98, Math.round(72 + cartCount * 4 + (subtotal > 0 ? 5 : 0)));
  }, [cartCount, products.length, subtotal]);

  const addToCart = (product) => {
    setCart((current) => {
      const currentQty = current[product.id] || 0;
      if (currentQty >= product.stock) return current;
      return { ...current, [product.id]: currentQty + 1 };
    });
  };

  const updateQuantity = (productId, nextQuantity) => {
    const product = products.find((item) => item.id === productId);
    if (!product) return;

    setCart((current) => {
      if (nextQuantity <= 0) {
        const copy = { ...current };
        delete copy[productId];
        return copy;
      }
      return { ...current, [productId]: Math.min(nextQuantity, product.stock) };
    });
  };

  const clearCart = () => setCart({});

  const handleCheckout = async ({ customerName, deliveryAddress, paymentMethod, couponCode }) => {
    const payload = {
      customer_name: customerName,
      delivery_address: deliveryAddress,
      payment_method: paymentMethod,
      coupon_code: couponCode,
      items: cartItems.map((item) => ({ product_id: item.id, quantity: item.quantity })),
    };

    const result = await checkoutCart(payload);
    setOrder(result);
    clearCart();
    return result;
  };

  const activities = useMemo(() => {
    const latestCart = cartItems.slice(0, 4).map((item) => ({
      actor: displayName,
      action: `added ${item.quantity} ×`,
      target: item.name,
      time: 'Now',
    }));

    const orderActivity = order
      ? [{ actor: displayName, action: 'completed order', target: order.order_id, time: 'Now' }]
      : [];

    return [
      ...orderActivity,
      ...latestCart,
      { actor: 'System', action: 'updated', target: `${lowStockProducts.length} low-stock alerts`, time: '11:45 AM' },
      { actor: 'FastAPI', action: 'served', target: 'protected products API', time: '11:40 AM' },
      { actor: 'React', action: 'synced', target: 'cart state in real time', time: '11:35 AM' },
    ].slice(0, 7);
  }, [cartItems, displayName, lowStockProducts.length, order]);

  return (
    <main className="dashboard-shell">
      <aside className="sidebar glass-card">
        <div>
          <div className="brand-lockup">
            <div className="brand-symbol">⌁</div>
            <div>
              <strong>Ware Sync</strong>
              <span>Product Dashboard</span>
            </div>
          </div>

          <button className="primary-btn add-item-btn" type="button" onClick={() => document.getElementById('storefront')?.scrollIntoView({ behavior: 'smooth' })}>
            <span>🛒</span> Browse Products <b>⌄</b>
          </button>

          <nav className="side-nav" aria-label="Dashboard sections">
            {navSections.map((item) => (
              item.admin ? (
                <button key={item.label} className="side-nav-button" type="button" onClick={onOpenAdmin}>
                  <span>{item.icon}</span>
                  {item.label}
                  <small>→</small>
                </button>
              ) : (
                <a key={item.label} className={item.active ? 'active' : ''} href={`#${item.target}`}>
                  <span>{item.icon}</span>
                  {item.label}
                  {['Inventory', 'Orders', 'Storefront'].includes(item.label) && <small>⌄</small>}
                </a>
              )
            ))}
          </nav>
        </div>

        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </aside>

      <section className="dashboard-main">
        <header className="topbar">
          <label className="search-box" aria-label="Search products">
            <span>⌕</span>
            <input
              type="search"
              placeholder="Search products, category, or action..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          <div className="top-actions">
            {canOpenAdmin && <button className="light-btn small" type="button" onClick={onOpenAdmin}>Admin CRUD</button>}
            <button className="icon-btn" type="button" aria-label="Notifications">🔔</button>
            <span className="low-stock-pill">{lowStockProducts.length} Low stock</span>
            <div className="profile-chip">
              <div className="profile-avatar">{displayName?.[0]?.toUpperCase() || 'U'}</div>
              <span>{displayName}</span>
              <small>{roleLabel}</small>
            </div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="primary-column">
            <div className="page-title-row">
              <div>
                <h1>Product Dashboard</h1>
                <p>Available for Admin, Staff, Viewer, and User roles. Browse products, monitor stock, and create persisted orders.</p>
              </div>
              <button className="primary-btn add-sale-btn" type="button" onClick={() => document.getElementById('storefront')?.scrollIntoView({ behavior: 'smooth' })}>+ New Product Order</button>
            </div>

            <section className="stats-grid" id="analytics">
              <StatCard icon="▣" label="Catalog items" value={products.length} hint="Loaded from FastAPI" tone="orange" />
              <StatCard icon="🛒" label="Items in cart" value={cartCount} hint="Live React state" tone="orange" />
              <StatCard icon="⚙" label="Cart efficiency" value={`${cartEfficiency}%`} hint="Demo conversion score" tone="orange" />
              <article className="countdown-card glass-card">
                <div>
                  <span>Next checkout review</span>
                  <strong>15 min</strong>
                </div>
                <em>Countdown time</em>
                <div className="timer-strip">14 : 30 : 54</div>
              </article>
            </section>

            {order && (
              <section className="order-success glass-card">
                <button aria-label="Close order confirmation" onClick={() => setOrder(null)}>×</button>
                <p className="eyebrow">Order confirmed</p>
                <h2>{order.order_id}</h2>
                <p>{order.message}</p>
                <strong>Total: {currency.format(order.summary.total)}</strong>
              </section>
            )}

            <section className="product-section" id="storefront">
              <div className="section-title-row">
                <div>
                  <h2><i className="dot green" /> Product catalog</h2>
                  <p>{filteredProducts.length} products available for add-to-cart actions</p>
                </div>
                <button className="light-btn" type="button">View all</button>
              </div>

              <div className="category-tabs" role="tablist" aria-label="Product categories">
                {availableCategories.map((item) => (
                  <button
                    key={item}
                    className={category === item ? 'active' : ''}
                    type="button"
                    onClick={() => setCategory(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>

              {loading && <div className="glass-card state-card">Loading protected products...</div>}
              {error && <div className="glass-card state-card error-text">{error}</div>}

              {!loading && !error && (
                <div className="product-grid">
                  {filteredProducts.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      quantityInCart={cart[product.id] || 0}
                      onAdd={() => addToCart(product)}
                    />
                  ))}
                </div>
              )}
            </section>

            <section className="product-section low-stock-section">
              <div className="section-title-row">
                <div>
                  <h2><i className="dot red" /> Low stock products</h2>
                  <p>Prioritize restocking before checkout demand increases.</p>
                </div>
                <button className="light-btn" type="button">View all</button>
              </div>

              <div className="compact-product-grid">
                {lowStockProducts.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    quantityInCart={cart[product.id] || 0}
                    onAdd={() => addToCart(product)}
                    compact
                  />
                ))}
              </div>
            </section>
          </section>

          <aside className="right-rail">
            <section className="activity-card glass-card">
              <div className="activity-head">
                <div>
                  <p className="eyebrow">Live activity</p>
                  <h2>Activity Feed</h2>
                </div>
                <label className="toggle-label">
                  Unreads
                  <span className="fake-toggle" />
                </label>
              </div>

              <div className="activity-list">
                {activities.map((activity, index) => (
                  <div className="activity-item" key={`${activity.actor}-${activity.target}-${index}`}>
                    <span>
                      <strong>@{activity.actor}</strong> {activity.action} <mark>{activity.target}</mark>
                    </span>
                    <time>{activity.time}</time>
                  </div>
                ))}
              </div>
            </section>

            <CartPanel
              cartItems={cartItems}
              subtotal={subtotal}
              onUpdateQuantity={updateQuantity}
              onClear={clearCart}
              onCheckout={handleCheckout}
            />
          </aside>
        </div>
      </section>
    </main>
  );
}
