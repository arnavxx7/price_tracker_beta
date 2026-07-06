"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface Product {
  // From product page scraper
  name?: string | null;
  brand_name?: string | null;
  country_code?: string | null;
  prod_url?: string | null;

  // From search results
  title?: string | null;
  url?: string | null;
  img_url?: string | null;
  org_price?: number | null;
  discount_percent?: number | null;
  prime?: boolean | null;

  // Shared fields
  asin: string | null;
  price: number | null;
  currency: string | null;
  rating: number | null;
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
  const router = useRouter();
  const prod_url = searchParams.get("url") ?? "";
  console.log("Amazon product url - ", prod_url)

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
        console.log(res)
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


  // Normalise fields — handle both search result shape and product scraper shape
  const displayName = product?.name ?? product?.title ?? null;
  const displayUrl = product?.prod_url ?? product?.url ?? null;
  const displayCountryCode = product?.country_code ?? "com";
  const currencySymbol = product?.currency
    ? (CURRENCY_SYMBOLS[product.currency] ?? product.currency)
    : "";

  function renderStars(rating: number) {
    const rounded = Math.round(rating);
    return (
      <>
        <span className="stars">
          {"★".repeat(rounded)}{"☆".repeat(5 - rounded)}
        </span>
        <span className="rating-num">{rating.toFixed(1)} / 5</span>
      </>
    );
  }
  
  console.log("Product details: ", product)
  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #0a0a0f;
          color: #e8e8f0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        /* ── Nav ── */
        .nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 32px;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .back-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          background: transparent;
          border: 1px solid rgba(255,255,255,0.1);
          color: #9090a8;
          font-size: 13px;
          padding: 7px 14px;
          border-radius: 8px;
          cursor: pointer;
          font-family: inherit;
          transition: all 0.15s;
        }
        .back-btn:hover { color: #e8e8f0; border-color: rgba(255,255,255,0.2); }
        .logo {
          font-size: 16px;
          font-weight: 700;
          color: #fff;
          letter-spacing: -0.3px;
        }
        .logo-icon { color: #7c6bff; margin-right: 6px; }

        /* ── Page ── */
        .page {
          max-width: 820px;
          margin: 0 auto;
          padding: 36px 16px 60px;
        }

        /* ── State messages ── */
        .state-message {
          text-align: center;
          padding: 100px 20px;
          color: #555;
          font-size: 0.95rem;
        }
        .state-error { color: #e05555; }

        /* ── Hero section ── */
        .product-hero {
          display: flex;
          gap: 28px;
          margin-bottom: 24px;
          background: #13131a;
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 16px;
          padding: 28px;
        }

        .product-image-wrapper {
          flex-shrink: 0;
          width: 160px;
          height: 160px;
          background: #1a1a24;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.06);
        }
        .product-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
          padding: 8px;
        }
        .product-image-placeholder {
          font-size: 0.72rem;
          color: #333;
        }

        .product-hero-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 14px;
          min-width: 0;
        }

        .product-title {
          font-size: 1.1rem;
          font-weight: 600;
          line-height: 1.5;
          color: #f0f0f8;
        }
        .product-title a {
          color: inherit;
          text-decoration: none;
        }
        .product-title a:hover { text-decoration: underline; }

        /* ── Badges row ── */
        .badges-row {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .badge {
          font-size: 0.68rem;
          padding: 3px 9px;
          border-radius: 5px;
          font-weight: 600;
          letter-spacing: 0.03em;
        }
        .badge-prime { background: #00a8e0; color: #fff; }
        .badge-asin  { background: #1e1e2e; color: #555; font-family: monospace; border: 1px solid #2a2a3a; }
        .badge-marketplace { background: #1e1e2e; color: #7c6bff; border: 1px solid rgba(124,107,255,0.2); }

        /* ── Price hero ── */
        .price-hero {
          display: flex;
          align-items: baseline;
          gap: 10px;
          flex-wrap: wrap;
        }
        .price-current {
          font-size: 2rem;
          font-weight: 800;
          color: #fff;
          letter-spacing: -1px;
        }
        .price-original {
          font-size: 1rem;
          color: #444;
          text-decoration: line-through;
        }
        .price-discount {
          font-size: 0.78rem;
          font-weight: 700;
          color: #4caf82;
          background: #0d2b1e;
          padding: 3px 9px;
          border-radius: 5px;
        }
        .price-unavailable { font-size: 0.9rem; color: #444; font-style: italic; }

        /* ── Fields grid ── */
        .section-label {
          font-size: 0.68rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: #3e3e56;
          margin-bottom: 12px;
          margin-top: 28px;
        }

        .fields-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1px;
          background: rgba(255,255,255,0.05);
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.06);
        }

        .field {
          background: #13131a;
          padding: 18px 22px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .field-label {
          font-size: 0.68rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #3e3e56;
        }
        .field-value {
          font-size: 0.92rem;
          color: #e8e8f0;
        }
        .field-value.muted { color: #2e2e46; font-style: italic; }
        .field-value.rating {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .stars { color: #f5a623; font-size: 0.85rem; letter-spacing: 1px; }
        .rating-num { font-size: 0.8rem; color: #555; }

        /* ── CTA row ── */
        .cta-row {
          display: flex;
          gap: 10px;
          margin-top: 24px;
          flex-wrap: wrap;
        }
        .btn-primary {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: linear-gradient(135deg, #7c6bff, #9f6bff);
          color: #fff;
          font-size: 13px;
          font-weight: 600;
          padding: 10px 20px;
          border-radius: 10px;
          text-decoration: none;
          transition: opacity 0.15s;
          font-family: inherit;
          border: none;
          cursor: pointer;
        }
        .btn-primary:hover { opacity: 0.85; }
        .btn-secondary {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: transparent;
          color: #9090a8;
          font-size: 13px;
          font-weight: 500;
          padding: 10px 20px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          text-decoration: none;
          transition: all 0.15s;
          cursor: pointer;
          font-family: inherit;
        }
        .btn-secondary:hover { color: #e8e8f0; border-color: rgba(255,255,255,0.2); }

        /* ── Chart placeholder ── */
        .chart-placeholder {
          margin-top: 28px;
          background: #13131a;
          border: 1px dashed rgba(124,107,255,0.2);
          border-radius: 16px;
          padding: 56px 28px;
          text-align: center;
          color: #2e2e46;
          font-size: 0.85rem;
        }
        .chart-placeholder span {
          display: block;
          font-size: 1.8rem;
          margin-bottom: 10px;
        }

        /* ── Responsive ── */
        @media (max-width: 560px) {
          .product-hero { flex-direction: column; }
          .product-image-wrapper { width: 100%; height: 200px; }
          .fields-grid { grid-template-columns: 1fr; }
          .nav { padding: 14px 16px; }
        }
      `}</style>

      {/* Nav */}
      <nav className="nav">
        <button className="back-btn" onClick={() => router.back()}>← Back</button>
        <span className="logo"><span className="logo-icon">⬡</span>PriceLens</span>
      </nav>

      <div className="page">
        {loading && (
          <div className="state-message"><p>Fetching product details...</p></div>
        )}

        {error && (
          <div className="state-message state-error"><p>{error}</p></div>
        )}

        {!loading && !error && !product && (
          <div className="state-message"><p>No product data found.</p></div>
        )}

        {!loading && !error && product && (
          <>
            {/* ── Hero ── */}
            <div className="product-hero">
              {/* Image */}
              <div className="product-image-wrapper">
                {product.img_url ? (
                  <img src={product.img_url} alt={displayName ?? "Product"} className="product-image" />
                ) : (
                  <div className="product-image-placeholder">No image</div>
                )}
              </div>

              <div className="product-hero-details">
                {/* Title */}
                <h1 className="product-title">
                  {displayUrl ? (
                    <a href={displayUrl} target="_blank" rel="noopener noreferrer">
                      {displayName ?? "Name unavailable"}
                    </a>
                  ) : (
                    displayName ?? <span style={{ color: "#333" }}>Name unavailable</span>
                  )}
                </h1>

                {/* Badges */}
                <div className="badges-row">
                  {product.prime && <span className="badge badge-prime">✓ Prime</span>}
                  {product.asin && <span className="badge badge-asin">ASIN: {product.asin}</span>}
                  <span className="badge badge-marketplace">amazon.{displayCountryCode}</span>
                </div>

                {/* Price */}
                <div className="price-hero">
                  {product.price != null ? (
                    <>
                      <span className="price-current">{currencySymbol}{product.price.toLocaleString()}</span>
                      {product.org_price != null && product.org_price !== product.price && (
                        <span className="price-original">{currencySymbol}{product.org_price.toLocaleString()}</span>
                      )}
                      {product.discount_percent != null && (
                        <span className="price-discount">{product.discount_percent}% off</span>
                      )}
                    </>
                  ) : (
                    <span className="price-unavailable">Price unavailable</span>
                  )}
                </div>
              </div>
            </div>

            {/* ── Details grid ── */}
            <p className="section-label">Product Details</p>
            <div className="fields-grid">

              <div className="field">
                <span className="field-label">Rating</span>
                {product.rating != null ? (
                  <span className="field-value rating">{renderStars(product.rating)}</span>
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
                <span className="field-label">Currency</span>
                <span className={`field-value ${!product.currency ? "muted" : ""}`}>
                  {product.currency ? `${product.currency} (${currencySymbol})` : "Unavailable"}
                </span>
              </div>

              <div className="field">
                <span className="field-label">Original Price</span>
                {product.org_price != null ? (
                  <span className="field-value">{currencySymbol}{product.org_price.toLocaleString()}</span>
                ) : (
                  <span className="field-value muted">Unavailable</span>
                )}
              </div>

              <div className="field">
                <span className="field-label">Discount</span>
                {product.discount_percent != null ? (
                  <span className="field-value" style={{ color: "#4caf82" }}>{product.discount_percent}% off</span>
                ) : (
                  <span className="field-value muted">Unavailable</span>
                )}
              </div>

              <div className="field">
                <span className="field-label">Prime</span>
                <span className={`field-value ${product.prime == null ? "muted" : ""}`}>
                  {product.prime == null ? "Unavailable" : product.prime ? "✓ Yes" : "✗ No"}
                </span>
              </div>

              <div className="field">
                <span className="field-label">ASIN</span>
                <span className={`field-value ${!product.asin ? "muted" : ""}`} style={{ fontFamily: "monospace" }}>
                  {product.asin ?? "Unavailable"}
                </span>
              </div>

              <div className="field">
                <span className="field-label">Marketplace</span>
                <span className="field-value">amazon.{displayCountryCode}</span>
              </div>

            </div>

            {/* ── CTAs ── */}
            <div className="cta-row">
              {displayUrl && (
                <a href={displayUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">
                  View on Amazon →
                </a>
              )}
              <button className="btn-secondary">🔔 Track Price</button>
            </div>

            {/* ── Chart placeholder ── */}
            <div className="chart-placeholder">
              <span>📈</span>
              Price history chart coming soon
            </div>
          </>
        )}
      </div>
    </>
  );
}
