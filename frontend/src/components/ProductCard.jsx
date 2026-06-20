const currency = new Intl.NumberFormat('en-PH', {
  style: 'currency',
  currency: 'PHP',
  maximumFractionDigits: 0,
});

export default function ProductCard({ product, quantityInCart, onAdd, compact = false }) {
  const isMaxed = quantityInCart >= product.stock;
  const isLowStock = product.stock <= 12;
  const stockPercent = Math.min(100, Math.round((product.stock / 35) * 100));
  const filledSegments = Math.max(1, Math.round(stockPercent / 10));

  return (
    <article className={`product-card glass-card ${compact ? 'compact' : ''}`}>
      <div className="product-card-top">
        <div className="product-avatar">
          <span>{product.image}</span>
          <small>{product.badge}</small>
        </div>

        <div className="product-title-block">
          <h3>{product.name}</h3>
          <p>{product.category}</p>
        </div>

        <span className={`status-pill ${isLowStock ? 'danger' : 'success'}`}>
          {isLowStock ? 'Low Stock' : 'In Stock'}
        </span>
      </div>

      {!compact && <p className="product-description">{product.description}</p>}

      <div className="product-task-row">
        <span>Stock progress:</span>
        <strong>{product.stock}/35 units</strong>
      </div>

      <div className="stock-progress" aria-label={`Stock level ${stockPercent}%`}>
        {Array.from({ length: 10 }).map((_, index) => (
          <i key={index} className={index < filledSegments ? 'filled' : ''} />
        ))}
      </div>

      <div className="product-task-row current-task">
        <span>{compact ? 'Price:' : 'Current action:'}</span>
        <strong>{compact ? currency.format(product.price) : `Add to cart  #PRD-${String(product.id).padStart(4, '0')}`}</strong>
      </div>

      <div className="product-footer-row">
        <div className="price-stack">
          <strong>{currency.format(product.price)}</strong>
          {product.compare_at_price && <del>{currency.format(product.compare_at_price)}</del>}
          <small>★ {product.rating}</small>
        </div>

        <div className="product-actions">
          <button className="text-btn" type="button">View Details</button>
          <button className="primary-btn small" type="button" disabled={isMaxed} onClick={onAdd}>
            {isMaxed ? 'Max' : quantityInCart ? `+${quantityInCart}` : 'Add Cart'}
          </button>
        </div>
      </div>
    </article>
  );
}
