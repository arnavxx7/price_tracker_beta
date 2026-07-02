"use client"

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

interface Product {
  asin: string | null;
  title: string | null;
  url: string | null;
  currency: string | null;
  price: number | null;
  original_price: number | null;
  discount_percent: number | null;
  img_url: string | null;
  rating: number | null;
  prime: boolean | null;
}

function PriceDisplay({ product }: { product: Product }) {
  const symbol = product.currency === "INR" ? "₹" : product.currency === "USD" ? "$" : product.currency ?? "";

  if (product.price == null && product.original_price == null) {
    return <span className="price-unavailable">Price unavailable</span>;
  }

  return (
    <div className="price-block">
      {product.price != null && (
        <span className="price-current">
          {symbol}{product.price.toLocaleString()}
        </span>
      )}
      {product.original_price != null && product.original_price !== product.price && (
        <span className="price-original">
          {symbol}{product.original_price.toLocaleString()}
        </span>
      )}
      {product.discount_percent != null && (
        <span className="price-discount">{product.discount_percent}% off</span>
      )}
    </div>
  );
}

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="product-card">
      <div className="product-image-wrapper">
        {product.img_url ? (
          <img
            src={product.img_url}
            alt={product.title ?? "Product image"}
            className="product-image"
          />
        ) : (
          <div className="product-image-placeholder">No image</div>
        )}
      </div>

      <div className="product-details">
        <div className="product-header">
          {product.title ? (
            <h2 className="product-title">
              {product.url ? (
                <a href={product.url} target="_blank" rel="noopener noreferrer">
                  {product.title}
                </a>
              ) : (
                product.title
              )}
            </h2>
          ) : (
            <h2 className="product-title muted">Title unavailable</h2>
          )}

          <div className="product-badges">
            {product.prime && (
              <span className="badge badge-prime">Prime</span>
            )}
            {product.asin && (
              <span className="badge badge-asin">ASIN: {product.asin}</span>
            )}
          </div>
        </div>

        <div className="product-meta">
          <PriceDisplay product={product} />

          {product.rating != null && (
            <div className="product-rating">
              <span className="rating-stars">
                {"★".repeat(Math.round(product.rating))}
                {"☆".repeat(5 - Math.round(product.rating))}
              </span>
              <span className="rating-value">{product.rating.toFixed(1)} / 5</span>
            </div>
          )}
        </div>

        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="view-btn"
          >
            View on Amazon →
          </a>
        )}
      </div>
    </div>
  );
}

export default function search_result() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") ?? "";
  console.log("This is the query received here at /search from home page:", query)

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;

    const fetchResults = async () => {
      setLoading(true);
      setError(null);

      try {
        // get response from fastapi for search url
        const stored = sessionStorage.getItem("searchResults");
        if (stored) {
          setProducts(JSON.parse(stored));
        } else {
          setError("No results found. Please search again.");
        }
        // const res = await fetch(`/api/search_query?q=${encodeURIComponent(query)}`);
        // if (!res.ok) throw new Error(`Server error: ${res.status}`);
        // const data: Product[] = await res.json();
        // setProducts(data);
      } catch (err) {
        setError("Failed to fetch results. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [query]);

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
          max-width: 960px;
          margin: 0 auto;
          padding: 32px 16px;
        }

        .page-header {
          margin-bottom: 28px;
          border-bottom: 1px solid #222;
          padding-bottom: 20px;
        }

        .page-header h1 {
          font-size: 1.1rem;
          font-weight: 500;
          color: #888;
        }

        .page-header h1 span {
          color: #e8e8e8;
          font-weight: 600;
        }

        .result-count {
          font-size: 0.82rem;
          color: #555;
          margin-top: 6px;
        }

        /* ── Cards ── */
        .product-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .product-card {
          display: flex;
          gap: 20px;
          background: #1a1a1a;
          border: 1px solid #2a2a2a;
          border-radius: 10px;
          padding: 18px;
          transition: border-color 0.15s;
        }

        .product-card:hover {
          border-color: #444;
        }

        /* ── Image ── */
        .product-image-wrapper {
          flex-shrink: 0;
          width: 110px;
          height: 110px;
          background: #111;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        .product-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .product-image-placeholder {
          font-size: 0.72rem;
          color: #444;
        }

        /* ── Details ── */
        .product-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 12px;
          min-width: 0;
        }

        .product-header {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .product-title {
          font-size: 0.95rem;
          font-weight: 500;
          line-height: 1.45;
          color: #e8e8e8;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .product-title a {
          color: inherit;
          text-decoration: none;
        }

        .product-title a:hover {
          color: #fff;
          text-decoration: underline;
        }

        .product-title.muted {
          color: #555;
        }

        /* ── Badges ── */
        .product-badges {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .badge {
          font-size: 0.7rem;
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 500;
          letter-spacing: 0.02em;
        }

        .badge-prime {
          background: #00a8e0;
          color: #fff;
        }

        .badge-asin {
          background: #2a2a2a;
          color: #666;
          font-family: monospace;
        }

        /* ── Price ── */
        .product-meta {
          display: flex;
          align-items: center;
          gap: 20px;
          flex-wrap: wrap;
        }

        .price-block {
          display: flex;
          align-items: baseline;
          gap: 8px;
          flex-wrap: wrap;
        }

        .price-current {
          font-size: 1.25rem;
          font-weight: 700;
          color: #fff;
        }

        .price-original {
          font-size: 0.85rem;
          color: #555;
          text-decoration: line-through;
        }

        .price-discount {
          font-size: 0.78rem;
          font-weight: 600;
          color: #4caf82;
          background: #0d2b1e;
          padding: 2px 7px;
          border-radius: 4px;
        }

        .price-unavailable {
          font-size: 0.85rem;
          color: #555;
        }

        /* ── Rating ── */
        .product-rating {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .rating-stars {
          color: #f5a623;
          font-size: 0.85rem;
          letter-spacing: 1px;
        }

        .rating-value {
          font-size: 0.78rem;
          color: #888;
        }

        /* ── CTA ── */
        .view-btn {
          align-self: flex-start;
          font-size: 0.8rem;
          color: #888;
          text-decoration: none;
          border: 1px solid #2a2a2a;
          padding: 5px 12px;
          border-radius: 6px;
          transition: all 0.15s;
          margin-top: auto;
        }

        .view-btn:hover {
          color: #e8e8e8;
          border-color: #444;
          background: #222;
        }

        /* ── States ── */
        .state-message {
          text-align: center;
          padding: 80px 20px;
          color: #555;
        }

        .state-message p {
          font-size: 1rem;
        }

        .state-error {
          color: #e05555;
        }

        /* ── Responsive ── */
        @media (max-width: 560px) {
          .product-card { flex-direction: column; }
          .product-image-wrapper { width: 100%; height: 160px; }
        }
      `}</style>

      <div className="page">
        <div className="page-header">
          <h1>
            Results for <span>&ldquo;{query}&rdquo;</span>
          </h1>
          {!loading && !error && products.length > 0 && (
            <p className="result-count">{products.length} products found</p>
          )}
        </div>

        {loading && (
          <div className="state-message">
            <p>Searching Amazon...</p>
          </div>
        )}

        {error && (
          <div className="state-message state-error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && products.length === 0 && query && (
          <div className="state-message">
            <p>No products found for &ldquo;{query}&rdquo;</p>
          </div>
        )}

        {!loading && !error && (
          <div className="product-list">
            {products.map((product, index) => (
              <ProductCard
                key={product.asin ?? index}
                product={product}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
