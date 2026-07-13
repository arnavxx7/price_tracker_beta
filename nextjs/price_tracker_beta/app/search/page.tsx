"use client"

import { timeStamp } from "console";
// import { unique } from "next/dist/build/utils";
import { useSearchParams, useRouter } from "next/navigation";
import { useRef, useEffect, useState } from "react";

interface Product {
  asin: string | null;
  title: string | null;
  url: string | null;
  currency: string | null;
  price: number | null;
  brand: string | null;
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
  const router = useRouter();
  function handleTitleClick() {
    if (!product.url) return;

    const productPageData = {
      name: product.title,
      price: product.price,
      currency: product.currency,
      brand_name: product.brand,         
      rating: product.rating,
      asin: product.asin,
      country_code: "com",        // since you're scraping amazon.com
      prod_url: product.url,
      org_price: product.original_price,
      discount_percent: product.discount_percent,
      img_url: product.img_url,
      prime: product.prime
    };
  
    sessionStorage.setItem("productData", JSON.stringify(productPageData));
    router.push(`/products?url=${encodeURIComponent(product.url ?? "")}`);
  }
  return (
    <div className="product-card animate-new-product" >
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
              <span
                onClick={handleTitleClick}
                className="title-link"
                style={{ cursor: product.url ? "pointer" : "default" }}
              >
                {product.title}
              </span>
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
  // console.log("This is the query received here at /search from home page:", query)

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scraping, setScraping] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const seenAsins = useRef<Set<string>>(new Set());
  const [total_products_db, setProductsDb] = useState(0);
  const [total_products_scraped, setProductsScraped] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const nextIndex = useRef<number>(0);  
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const jobKey = `scrape_job_${query}`;

  useEffect(() => {
    if (!query) return;

    const cacheKey = `search_${query}`;
    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
      const {products: cachedProducts, asins: cachedasins, job_id: cached_job_id} = JSON.parse(cached);

      seenAsins.current = new Set(cachedasins);
      setProducts(cachedProducts);
      setLoading(false);
      // checking if a job is still running
      if (cached_job_id) {
        setJobId(cached_job_id);
        checkAndResumePoll(cached_job_id, cacheKey);
      }

      return;
    }
    else {
      sessionStorage.removeItem(cacheKey);
    }

    // Reset state on new query
    setProducts([]);
    setLoading(true);
    setScraping(false);
    setError(null);
    seenAsins.current = new Set();
    nextIndex.current = 0;
    

    const init = async () => {
      try {
        // Shwoing db results instantly
        const dbRes = sessionStorage.getItem("searchResultsDB");
        if (dbRes) {
          const parsed: Product[] = JSON.parse(dbRes);
          const unique = dedupe(parsed, seenAsins.current);
          setProductsDb(unique.length);
          setProducts(unique);
          nextIndex.current = unique.length;
          saveToCache(cacheKey, unique, null);
        }
        setLoading(false);
        // Starting background scraping job
        const start_scrape_res = await fetch(`/api/start_scrape?q=${encodeURIComponent(query)}`);
        const start_scrape_data = await start_scrape_res.json();
        const id = start_scrape_data.job_id;
        setJobId(id);
        // Saving the newly created job id in cache,
        saveToCache(cacheKey, products, id);
        // Start polling  - sending api requests every 3s
        startPolling(id, cacheKey);
      }
      catch (err) {
        setError("Failed to fetch results");
        setLoading(false);
        console.error(err);
      }
    };

    init();

    // const fetchResults = async () => {

    //   try {
    //     // get response from fastapi database endpoint for search url
    //     const stored = sessionStorage.getItem("searchResults");
    //     if (stored) {
    //         const parsed: Product[] = JSON.parse(stored);
    //         // Deduplicate by ASIN, keeping first occurrence
    //         // const seen = new Set<string>();
    //         // const unique = parsed.filter(product => {
    //         //   if (!product.asin) return true; // keep products without ASIN
    //         //   if (seen.has(product.asin)) return false;
    //         //   seen.add(product.asin);
    //         //   return true;
    //         // });
    //         const unique = dedupe(parsed, seenAsins.current);
    //         setProductsDb(unique.length);
    //         setProducts(unique);
    //     } 
    //     // else {
    //     //   setError("No results found. Please search again.");
    //     // }
        
    //     setLoading(false);
    //     // Step 2 — open SSE stream for live scrape results
    //     setScraping(true);
    //     let total_products_scraped = 0;
    //     eventSource = new EventSource(
    //       `/api/scrape_stream?q=${encodeURIComponent(query)}`
    //     );
        
    //     eventSource.onmessage = (event) => {
    //       const msg = JSON.parse(event.data);
    //       console.log("This is the status of the new message received by event source = ", msg.status);
          
    //       if (msg.status === "success") {
    //         console.log(`Found ${msg.num_products} products on page: ${msg.page}`)
    //         setCurrentPage(msg.page)
    //         const newOnes = dedupe(msg.content, seenAsins.current);
      
    //         if (newOnes.length > 0) {
    //           // append the products list with the new products received, and save them in cache
    //           setProducts(prev => {
    //               const updated = [...prev, ...newOnes]; // append the products list with new ones
    //               sessionStorage.setItem(cacheKey, JSON.stringify({  // save them in cache
    //                 products: updated,
    //                 asins: Array.from(seenAsins.current),
    //                 timeStamp: Date.now()
    //               }));
    //           return updated;   // return the updated list
    //           }
    //           );

    //         }
    //         setProductsScraped(prevCount => prevCount + newOnes.length);
            
    //       }

    //       if (msg.status === "done" || msg.status === "error") {
    //         setScraping(false);
    //         eventSource?.close();
    //         //  IN CASE OF DONE OR ERROR JUST SAVE THE LATEST LIST OF PRODUCTS IN THE CACHE
    //         setProducts(prev => {
    //           sessionStorage.setItem(cacheKey, JSON.stringify({
    //             products: prev,
    //             asins: Array.from(seenAsins.current),
    //             timestamp: Date.now()
    //           }));
    //           return prev;
    //         });
    //       }

    //       if (msg.status === "error") {
    //         console.log(`Recevied following error on page ${msg.page}: ${msg.details}`)
    //       }

    //     };

    //     eventSource.onerror = () => {
    //       setScraping(false);
    //       eventSource?.close();
    //     };


    //     // const res = await fetch(`/api/search_query?q=${encodeURIComponent(query)}`);
    //     // if (!res.ok) throw new Error(`Server error: ${res.status}`);
    //     // const data: Product[] = await res.json();
    //     // setProducts(data);
    //   } catch (err) {
    //     setError("Failed to fetch results. Please try again.");
    //     setScraping(false);
    //     console.error(err);
    //   } finally {
    //     setLoading(false);
    //   }
    // };

    // fetchResults();

    return () => {
        // Don't stop the scrape — just stop polling
        if (pollRef.current) clearInterval(pollRef.current);
      };
    
  }, [query]);

  
  // Dedupe helper — mutates the seen set
  function dedupe(list: Product[], seen: Set<string>): Product[] {
    return list.filter(p => {
      if (!p.asin) return true;
      if (seen.has(p.asin)) return false;
      seen.add(p.asin);
      return true;
    });
  }

  function startPolling(id: string, cacheKey: string) {
    setScraping(true);

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(
          `/api/scrape_status?since_index=${nextIndex.current}&job_id=${id}&q=${query}`
        )
        const data = await res.json();
        
        if (data.new_products?.length > 0) {
        const newOnes = dedupe(data.new_products, seenAsins.current);
        if (newOnes.length > 0) {
          setProducts(prev => {
            const updated = [...prev, ...newOnes];
            saveToCache(cacheKey, updated, id);
            return updated;
          });
        }
      }

      // Advance index regardless (skip already-seen products)
      nextIndex.current = data.next_index;
      setCurrentPage(data.page);

      if (data.status === "done" || data.status === "not_found") {
        setScraping(false);
        if (pollRef.current) clearInterval(pollRef.current);
      }
      }
      catch (err) {
        console.error("Poll error: ", err);
      } 
    }, 3000) // check every 3s
  }

  async function checkAndResumePoll(id:  string, cacheKey: string) {
      // Check if job is still running before resuming poll
    try {
      const res = await fetch(`/api/scrape_status?since_index=${nextIndex.current}&job_id=${id}&q=${query}`);
      const data = await res.json();

      if (data.status === "running") {
        setScraping(true);
        startPolling(id, cacheKey);
      }
      // If done, do nothing — cached results are already shown
    } catch (err) {
      console.error("Resume poll check failed:", err);
    }
  }

  function saveToCache(cacheKey: string, prods: Product[], id: string | null) {
  sessionStorage.setItem(cacheKey, JSON.stringify({
    products: prods,
    asins: Array.from(seenAsins.current),
    timestamp: Date.now(),
    job_id: id
  }));
  }



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
        
        .title-link {
          color: inherit;
          text-decoration: none;
        }
        .title-link:hover {
          color: #fff;
          text-decoration: underline;
        }

        .scraping-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.78rem;
          color: #7c6bff;
          margin-bottom: 16px;
          padding: 8px 14px;
          background: rgba(124, 107, 255, 0.08);
          border: 1px solid rgba(124, 107, 255, 0.15);
          border-radius: 8px;
          width: fit-content;
        }
        .scraping-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background-color: #ef4444; /* Red dot */
          animation: pulse 1.2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.4; transform: scale(0.75); }
        }

        .header-stats {
          display: flex;
          align-items: center;
          gap: 1rem; /* Space between the badges */
          font-size: 0.9rem;
        }

        /* Base style for the little stat pills */
        .stat-badge {
          padding: 0.4rem 0.8rem;
          border-radius: 9999px; /* Rounds the edges like a pill */
          background-color: #f3f4f6; /* Light gray */
          color: #374151;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        } 
        
        .total-stat {
          background-color: #111;
          color: white;
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

          {/* Right side: Live Stats */}
          {!loading && !error && (
            <div className="header-stats">
              <span className="stat-badge db-stat">
                <strong>{total_products_db}</strong> from DB
              </span>
              
              <span className="stat-badge live-stat">
                {scraping && <span className="scraping-dot" />}
                <strong>{total_products_scraped}</strong> scraped live
              </span>
              
              <span className="stat-badge total-stat">
                <strong>{products.length}</strong> total
              </span>
            </div>
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
                key={product.asin ?? `no-asin-${index}`}
                product={product}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
