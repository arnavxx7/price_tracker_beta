"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

interface Product {
  name: string | null;
  price: number | null;
  currency: string | null;
  brand_name: string | null;
  rating: number | null;
  asin: string | null;
  country_code: string | null;
  prod_url: string | null;
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  INR: "₹",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
};

export default function ProductPage() {
  const searchParams = useSearchParams();
  const prod_url = searchParams.get("q") ?? "";

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!prod_url) return;

    const fetchProduct = async () => {
      setLoading(true);
      setError(null);

      try {
        //  get response from fastapi for product url
        const res = sessionStorage.getItem("productData");
        if (res) {
          setProduct(JSON.parse(res));
        } else {
          setError("No product data found. Please try again.");
        }
        // const res = await fetch(
        //   `/api/search_query?q=${encodeURIComponent(prod_url)}`
        // );
        // if (!res.ok) throw new Error(`Server error: ${res.status}`);
        // const data: Product = await res.json();
        // setProduct(data);
      } catch (err) {
        setError("Failed to fetch product details. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [prod_url]);

  const currencySymbol = product?.currency
    ? (CURRENCY_SYMBOLS[product.currency] ?? product.currency)
    : "";

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #0f0f0f;
          color: #e8e8e8;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .page {
          max-width: 760px;
          margin: 0 auto;
          padding: 40px 16px;
        }

        /* ── State messages ── */
        .state-message {
          text-align: center;
          padding: 100px 20px;
          color: #555;
          font-size: 0.95rem;
        }

        .state-error { color: #e05555; }

        /* ── Card ── */
        .product-card {
          background: #1a1a1a;
          border: 1px solid #2a2a2a;
          border-radius: 12px;
          overflow: hidden;
        }

        /* ── Card header ── */
        .card-header {
          padding: 28px 28px 24px;
          border-bottom: 1px solid #222;
        }

        .product-name {
          font-size: 1.15rem;
          font-weight: 600;
          line-height: 1.5;
          color: #f0f0f0;
          margin-bottom: 12px;
        }

        .product-name a {
          color: inherit;
          text-decoration: none;
        }

        .product-name a:hover {
          text-decoration: underline;
        }

        .asin-badge {
          display: inline-block;
          font-size: 0.7rem;
          font-family: monospace;
          color: #555;
          background: #222;
          border: 1px solid #2a2a2a;
          padding: 3px 8px;
          border-radius: 4px;
        }

        /* ── Fields grid ── */
        .fields-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1px;
          background: #222;
        }

        .field {
          background: #1a1a1a;
          padding: 20px 28px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .field-label {
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #555;
        }

        .field-value {
          font-size: 0.95rem;
          color: #e8e8e8;
        }

        .field-value.price {
          font-size: 1.5rem;
          font-weight: 700;
          color: #fff;
        }

        .field-value.muted {
          color: #444;
          font-style: italic;
        }

        .field-value.rating {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stars {
          color: #f5a623;
          font-size: 0.9rem;
          letter-spacing: 1px;
        }

        .rating-num {
          font-size: 0.85rem;
          color: #888;
        }

        /* ── Footer ── */
        .card-footer {
          padding: 20px 28px;
          border-top: 1px solid #222;
        }

        .view-btn {
          display: inline-block;
          font-size: 0.82rem;
          color: #888;
          text-decoration: none;
          border: 1px solid #2a2a2a;
          padding: 8px 16px;
          border-radius: 6px;
          transition: all 0.15s;
        }

        .view-btn:hover {
          color: #e8e8e8;
          border-color: #444;
          background: #222;
        }

        /* ── Chart placeholder ── */
        .chart-placeholder {
          margin-top: 20px;
          background: #1a1a1a;
          border: 1px dashed #2a2a2a;
          border-radius: 12px;
          padding: 48px 28px;
          text-align: center;
          color: #333;
          font-size: 0.85rem;
        }

        /* ── Responsive ── */
        @media (max-width: 520px) {
          .fields-grid { grid-template-columns: 1fr; }
          .card-header, .field, .card-footer { padding: 18px; }
        }
      `}</style>

      <div className="page">
        {loading && (
          <div className="state-message">
            <p>Fetching product details...</p>
          </div>
        )}

        {error && (
          <div className="state-message state-error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && !product && (
          <div className="state-message">
            <p>No product URL provided.</p>
          </div>
        )}

        {!loading && !error && product && (
          <>
            <div className="product-card">

              {/* Header — name + ASIN */}
              <div className="card-header">
                <h1 className="product-name">
                  {product.prod_url ? (
                    <a href={product.prod_url} target="_blank" rel="noopener noreferrer">
                      {product.name ?? "Name unavailable"}
                    </a>
                  ) : (
                    product.name ?? <span style={{ color: "#444" }}>Name unavailable</span>
                  )}
                </h1>
                {product.asin && (
                  <span className="asin-badge">ASIN: {product.asin}</span>
                )}
              </div>

              {/* Fields grid */}
              <div className="fields-grid">

                <div className="field">
                  <span className="field-label">Price</span>
                  {product.price != null ? (
                    <span className="field-value price">
                      {currencySymbol}{product.price.toLocaleString()}
                    </span>
                  ) : (
                    <span className="field-value muted">Unavailable</span>
                  )}
                </div>

                <div className="field">
                  <span className="field-label">Brand</span>
                  <span className={`field-value ${!product.brand_name ? "muted" : ""}`}>
                    {product.brand_name ?? "Unavailable"}
                  </span>
                </div>

                <div className="field">
                  <span className="field-label">Rating</span>
                  {product.rating != null ? (
                    <span className="field-value rating">
                      <span className="stars">
                        {"★".repeat(Math.round(product.rating))}
                        {"☆".repeat(5 - Math.round(product.rating))}
                      </span>
                      <span className="rating-num">{product.rating.toFixed(1)} / 5</span>
                    </span>
                  ) : (
                    <span className="field-value muted">Unavailable</span>
                  )}
                </div>

                <div className="field">
                  <span className="field-label">Currency</span>
                  <span className={`field-value ${!product.currency ? "muted" : ""}`}>
                    {product.currency
                      ? `${product.currency} (${currencySymbol})`
                      : "Unavailable"}
                  </span>
                </div>

                <div className="field">
                  <span className="field-label">Marketplace</span>
                  <span className={`field-value ${!product.country_code ? "muted" : ""}`}>
                    {product.country_code
                      ? `amazon.${product.country_code}`
                      : "Unavailable"}
                  </span>
                </div>

                <div className="field">
                  <span className="field-label">ASIN</span>
                  <span className={`field-value ${!product.asin ? "muted" : ""}`}
                    style={{ fontFamily: "monospace" }}>
                    {product.asin ?? "Unavailable"}
                  </span>
                </div>

              </div>

              {/* Footer */}
              {product.prod_url && (
                <div className="card-footer">
                  <a
                    href={product.prod_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="view-btn"
                  >
                    View on Amazon →
                  </a>
                </div>
              )}
            </div>

            {/* Price history chart placeholder */}
            <div className="chart-placeholder">
              Price history chart coming soon
            </div>
          </>
        )}
      </div>
    </>
  );
}
