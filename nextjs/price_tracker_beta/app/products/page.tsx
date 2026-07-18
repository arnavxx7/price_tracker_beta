"use client";

// import { fetchExternalImage } from "next/dist/server/image-optimizer";
import { useSearchParams, useRouter } from "next/navigation";
// import { parse } from "path";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import LoginModal from "../components/login_modal";
import { RechartsDevtools } from '@recharts/devtools';
import { supabase } from "../utils/supabase";
import { useEffect, useMemo, useState } from "react";

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
  source?: "db" | "scraped" | null;

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
  // console.log("Amazon product url - ", prod_url)

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [price_points, setPricePoints] = useState([]);
  const [isLoginModalOpen, setLoginModalOpen] = useState<boolean>(false);

  useEffect(() => {
    if (!prod_url) return;

    const fetchProduct = async () => {
      setLoading(true);
      setError(null);

      try {
        //  get response from fastapi for product url
        const res = sessionStorage.getItem("productData");
        console.log("This is the product information = ", res);
        if (res) {
          const parsedProduct = JSON.parse(res);
          setProduct(parsedProduct);
            
          if (parsedProduct && parsedProduct.asin) {
            const price_chart_res = await fetch(
              `/api/price_chart?asin=${encodeURIComponent(parsedProduct.asin)}`
            );

            if (price_chart_res.ok) {
              const chartData = await price_chart_res.json();

              if (chartData.status === "success" && chartData.dp) {
                  setPricePoints(chartData.dp);
              }
            }
            else {
              console.error(`Failed to fetch price chart data points: ${price_chart_res}`)
            }
          }
          
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

  const [userLoggedInFlag, setUserLoggedInFlag] = useState<boolean>(false);

  useEffect(() => {
    // checking if the user is already logged in when the page loads
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUserLoggedInFlag(!!session); // true if session exists, false if null
    };
    checkUser();
    
    // listening for the moment the user clicks the magic link
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserLoggedInFlag(!!session);
    });

    return () => subscription.unsubscribe()
  }, []);

  const [targetPrice, setTargetPrice] = useState<number>(0.00);

  useEffect(() => {
    if (product?.price) {
        setTargetPrice(product.price - 10);
    }
    }, [product]); // runs whenever product changes

  // Normalise fields — handle both search result shape and product scraper shape
  const displayName = product?.name ?? product?.title ?? null;
  const displayUrl = product?.prod_url ?? product?.url ?? null;
  const displayCountryCode = product?.country_code ?? "com";
  const currencySymbol = product?.currency
    ? (CURRENCY_SYMBOLS[product.currency] ?? product.currency)
    : "";

  // Computing the stats
  const { lowestPrice, highestPrice, averagePrice } = useMemo(() => {
    if (!price_points || price_points.length === 0) {
      return {
        lowestPrice: product?.price ?? 0,
        highestPrice: product?.org_price ?? product?.price ?? 0,
        averagePrice: product?.price ?? 0,
      };
    }

  const prices = price_points.map((dp: any) => dp.price).filter((p) => p != null);
    console.log("Prices from price_points = ", prices);
    if (prices.length === 0) {
            return {
        lowestPrice: product?.price ?? 0,
        highestPrice: product?.org_price ?? product?.price ?? 0,
        averagePrice: product?.price ?? 0,
      };
    }

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const avg = prices.reduce((a, b) => a + b, 0) / prices.length;

  return {
      lowestPrice: min,
      highestPrice: max,
      averagePrice: Math.round(avg)
    };
  
  }, [price_points, product]);

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

  function handleLogin() {

      if (!userLoggedInFlag) {
        setLoginModalOpen(true);
      }
      else {
        console.log("User already logged in, proceeding to set price alert");
   
      }
  }


  const handlePriceAlert = async (target_price: number) => {
    // fexcthing the logged in user
    const { data: {user} } = await supabase.auth.getUser();

    const alert_json = {
      user_id: user?.id,
      asin: product?.asin,
      target_price: target_price,
      current_price: product?.price,
      is_active: true,
    }
    console.log("Alert creation: sending following json to Fastapi backend", alert_json);
    try {
      const res = await fetch(`/api/alerts/create`, {
        method: "POST",
        headers: {"Content-Type" : "application/json"},
        body: JSON.stringify(alert_json)
      });

      const data = await res.json();
      console.log("Alert created:", data);
    } catch(err) {
      console.error("Failed to create alert: ", err);
    }

  }
  // console.log("Product details: ", product)
  console.log("These are the price points fetched: ", price_points);
  
  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #111116;
          color: #e8e8f0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        /* ── Nav ── */
        .nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 24px;
          background: #1a1a21;
          border-bottom: 1px solid #2a2a35;
        }
        .back-btn {
          background: transparent;
          border: none;
          color: #9090a8;
          font-size: 14px;
          cursor: pointer;
          font-family: inherit;
          transition: color 0.15s;
        }
        .back-btn:hover { color: #e8e8f0; }
        .logo {
          font-size: 18px;
          font-weight: 500;
          color: #fff;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .logo-icon { color: #3b82f6; font-size: 20px; } /* Blue hex icon */

        /* ── Layout ── */
        .dashboard-container {
          max-width: 1100px;
          margin: 0 auto;
          padding: 24px 16px 60px;
          display: grid;
          grid-template-columns: 1.4fr 1fr;
          gap: 20px;
          align-items: start;
        }
        @media (max-width: 860px) {
          .dashboard-container { grid-template-columns: 1fr; }
        }

        /* ── Shared Card Styles ── */
        .card {
          background: #1c1c22;
          border: 1px solid #2a2a35;
          border-radius: 12px;
          padding: 24px;
          display: flex;
          flex-direction: column;
        }
        .card-header {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #9090a8;
          margin-bottom: 16px;
        }
        
        .col-left { display: flex; flex-direction: column; gap: 20px; }
        .col-right { display: flex; flex-direction: column; gap: 20px; }

        /* ── Product Hero Card ── */
        .product-hero {
          display: flex;
          gap: 24px;
        }
        .product-img-box {
          width: 140px;
          height: 140px;
          background: #111116;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          border: 1px solid #2a2a35;
          padding: 12px;
        }
        .product-img-box img {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }
        .product-info {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .badges-row { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
        .badge {
          font-size: 0.7rem;
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 500;
        }
        .badge-domain { background: #115e59; color: #4ade80; } /* Dark green bg, light green text */
        .badge-prime { color: #f59e0b; font-weight: 600; font-size: 0.8rem; }
        
        .product-title {
          font-size: 1.25rem;
          font-weight: 600;
          line-height: 1.3;
          color: #fff;
          margin-bottom: 4px;
        }
        
        .price-row {
          display: flex;
          align-items: baseline;
          gap: 12px;
          margin: 4px 0;
        }
        .current-price { font-size: 2.2rem; font-weight: 700; color: #fff; }
        .original-price { font-size: 1.1rem; color: #6b7280; text-decoration: line-through; }
        
        .discount-pill {
          background: #064e3b;
          color: #22c55e;
          font-size: 0.75rem;
          font-weight: 600;
          padding: 4px 10px;
          border-radius: 6px;
          width: fit-content;
          margin-bottom: 8px;
        }

        .meta-row {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
          color: #9ca3af;
        }
        .rating-flex { display: flex; align-items: center; gap: 6px; }
        .stars { color: #fbbf24; font-size: 1rem; }

        /* ── Stats Grid ── */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
        }
        .stat-card {
          background: #1c1c22;
          border: 1px solid #2a2a35;
          border-radius: 12px;
          padding: 20px;
          text-align: center;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .stat-label { font-size: 0.75rem; color: #9090a8; text-transform: uppercase; font-weight: 600; }
        .stat-val { font-size: 1.75rem; font-weight: 600; }
        .val-low { color: #22c55e; }
        .val-avg { color: #fff; }
        .val-high { color: #ef4444; }

        /* ── Price History Chart ── */
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .chart-title { font-size: 1rem; font-weight: 600; color: #fff; }
        .chart-filters {
          display: flex;
          background: #111116;
          border-radius: 6px;
          border: 1px solid #2a2a35;
          overflow: hidden;
        }
        .filter-btn {
          background: transparent;
          border: none;
          color: #9090a8;
          padding: 6px 14px;
          font-size: 0.8rem;
          cursor: pointer;
          border-right: 1px solid #2a2a35;
        }
        .filter-btn:last-child { border-right: none; }
        .filter-btn.active { background: #1e3a8a; color: #fff; } /* Dark blue */
        
        .chart-area {
          height: 250px;
          background: #111116;
          border-radius: 8px;
          border: 1px dashed #2a2a35;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        /* ── Product Details Grid ── */
        .details-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0;
          border: 1px solid #2a2a35;
          border-radius: 8px;
          overflow: hidden;
        }
        .detail-item {
          padding: 16px;
          background: #111116;
          display: flex;
          flex-direction: column;
          gap: 6px;
          border-right: 1px solid #2a2a35;
          border-bottom: 1px solid #2a2a35;
        }
        .detail-item:nth-child(even) { border-right: none; }
        .detail-item:nth-last-child(-n+2) { border-bottom: none; }
        .d-label { font-size: 0.7rem; color: #9090a8; text-transform: uppercase; }
        .d-value { font-size: 1rem; color: #fff; font-weight: 500; }

        /* ── Deal Score ── */
        .gauge-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin: 10px 0;
        }
        .gauge-svg { width: 200px; height: 100px; }
        .score-val { font-size: 2rem; font-weight: 700; color: #fff; margin-top: -40px; text-align: center; }
        .score-sub { font-size: 0.8rem; color: #9090a8; }
        .score-text { font-size: 1.1rem; color: #22c55e; font-weight: 500; margin-top: 8px; }
        .score-desc { font-size: 0.85rem; color: #9090a8; margin-top: 4px; }

        /* ── Best Time To Buy ── */
        .time-filters { display: flex; gap: 8px; margin-bottom: 16px; }
        .time-pill {
          background: #111116;
          border: 1px solid #2a2a35;
          color: #9090a8;
          padding: 6px 14px;
          border-radius: 6px;
          font-size: 0.85rem;
          cursor: pointer;
        }
        .time-pill.active { background: #1e3a8a; color: #fff; border-color: #1e3a8a; }
        .prediction-box {
          background: #052e16;
          border: 1px solid #064e3b;
          border-radius: 8px;
          padding: 16px;
        }
        .pred-title { color: #22c55e; font-weight: 500; font-size: 0.95rem; margin-bottom: 4px; }
        .pred-desc { color: #16a34a; font-size: 0.85rem; }

        /* ── Set Price Alert ── */
        .alert-form { display: flex; flex-direction: column; gap: 12px; }
        .input-group {
          display: flex;
          align-items: center;
          background: #111116;
          border: 1px solid #2a2a35;
          border-radius: 8px;
          padding: 0 12px;
          height: 44px;
        }
        .input-group span { color: #9090a8; font-size: 1rem; margin-right: 8px; }
        .input-group input {
          background: transparent;
          border: none;
          color: #fff;
          font-size: 1rem;
          width: 100%;
          outline: none;
        }
        .input-group input::placeholder { color: #6b7280; }
        .btn-outline {
          background: transparent;
          border: 1px solid #1e3a8a;
          color: #60a5fa;
          height: 44px;
          border-radius: 8px;
          font-size: 0.95rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }
        .btn-outline:hover { background: #1e3a8a; color: #fff; }

        /* ── Buy Button ── */
        .btn-buy {
          background: #3b82f6; /* Bright blue */
          color: #fff;
          border: none;
          height: 54px;
          border-radius: 8px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          width: 100%;
          transition: background 0.2s;
        }
        .btn-buy:hover { background: #2563eb; }

      `}</style>

      {/* ── Top Navigation ── */}
      <nav className="nav">
        <span className="logo">
          <span className="logo-icon">⬡</span>PriceLens
        </span>
        <button className="back-btn" onClick={() => router.back()}>
          ← Back to results
        </button>
      </nav>

      <div className="dashboard-container">
        {loading && <div style={{ textAlign: "center", width: "100%", padding: "50px", color: "#888" }}>Fetching product details...</div>}
        {error && <div style={{ textAlign: "center", width: "100%", padding: "50px", color: "#ef4444" }}>{error}</div>}

        {!loading && !error && product && (
          <>
            {/* ── LEFT COLUMN ── */}
            <div className="col-left">
              
              {/* Product Hero Card */}
              <div className="card product-hero">
                <div className="product-img-box">
                  {product.img_url ? (
                    <img src={product.img_url} alt={displayName ?? "Product"} />
                  ) : (
                    <span style={{ fontSize: "24px", color: "#444" }}>No Image</span>
                  )}
                </div>
                <div className="product-info">
                  <div className="badges-row">
                    <span className="badge badge-domain">amazon.{displayCountryCode}</span>
                    {product.prime && <span className="badge badge-prime">✓ Prime</span>}
                  </div>
                  <h1 className="product-title">{displayName ?? "Name unavailable"}</h1>
                  
                  <div className="price-row">
                    <span className="current-price">{currencySymbol}{(product.price ?? 0).toLocaleString()}</span>
                    {product.org_price != null && product.price != null && product.org_price > product.price && (
                      <span className="original-price">{currencySymbol}{product.org_price.toLocaleString()}</span>
                    )}
                  </div>
                  
                  {product.discount_percent != null && product.discount_percent > 0 && (
                    <div className="discount-pill">{product.discount_percent}% off</div>
                  )}

                  <div className="meta-row">
                    {product.rating != null && renderStars(product.rating)}
                    <span>·</span>
                    <span>{product.brand_name ?? "Unknown Brand"}</span>
                    <span>·</span>
                    <span>ASIN: {product.asin ?? "N/A"}</span>
                  </div>
                </div>
              </div>

              {/* Stats Row */}
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-label">Lowest Ever</span>
                  <span className="stat-val val-low">{currencySymbol}{lowestPrice.toLocaleString()}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Average</span>
                  <span className="stat-val val-avg">{currencySymbol}{averagePrice.toLocaleString()}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Highest Ever</span>
                  <span className="stat-val val-high">{currencySymbol}{highestPrice.toLocaleString()}</span>
                </div>
              </div>

              {/* Price History Chart */}
              <div className="card">
                <div className="chart-header">
                  <span className="chart-title">Price history</span>
                  <div className="chart-filters">
                    <button className="filter-btn active">1M</button>
                    <button className="filter-btn">3M</button>
                    <button className="filter-btn">All</button>
                  </div>
                </div>
                
                <div className="chart-area" style={{ padding: price_points.length > 0 ? "10px" : "0" }}>
                  {price_points.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={price_points}
                        margin={{ top: 5, right: 0, left: -20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a35" vertical={false} />
                        <XAxis dataKey="date_yaxis" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${currencySymbol}${val}`} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1c1c22', borderColor: '#2a2a35', color: '#fff' }}
                          itemStyle={{ color: '#60a5fa' }}
                        />
                        <Line
                          type="monotone"
                          dataKey="price"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 6, fill: '#3b82f6', stroke: '#111116', strokeWidth: 2 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: "center", color: "#6b7280" }}>
                      <span style={{ fontSize: "24px", display: "block", marginBottom: "8px" }}>📈</span>
                      Chart data unavailable
                    </div>
                  )}
                </div>
              </div>

              {/* Product Details */}
              <div className="card" style={{ padding: "0", background: "transparent", border: "none" }}>
                <span className="card-header" style={{ marginBottom: "12px" }}>Product Details</span>
                <div className="details-grid">
                  <div className="detail-item">
                    <span className="d-label">Brand</span>
                    <span className="d-value">{product.brand_name ?? "Unavailable"}</span>
                  </div>
                  <div className="detail-item">
                    <span className="d-label">Currency</span>
                    <span className="d-value">{product.currency ? `${product.currency} (${currencySymbol})` : "Unavailable"}</span>
                  </div>
                  <div className="detail-item">
                    <span className="d-label">ASIN</span>
                    <span className="d-value">{product.asin ?? "Unavailable"}</span>
                  </div>
                  <div className="detail-item">
                    <span className="d-label">Marketplace</span>
                    <span className="d-value">amazon.{displayCountryCode}</span>
                  </div>
                </div>
              </div>

            </div>

            {/* ── RIGHT COLUMN ── */}
            <div className="col-right">
              
              {/* Deal Score */}
              <div className="card">
                <span className="card-header">Deal Score</span>
                <div className="gauge-container">
                  {/* Fake SVG Gauge to match image */}
                  <svg viewBox="0 0 100 50" className="gauge-svg">
                    <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#2a2a35" strokeWidth="8" strokeLinecap="round" />
                    {/* The green progress arc (approx 72%) */}
                    <path d="M 10 50 A 40 40 0 0 1 70 15" fill="none" stroke="#10b981" strokeWidth="8" strokeLinecap="round" />
                  </svg>
                  <div className="score-val">72</div>
                  <div className="score-sub">out of 100</div>
                  <div className="score-text">Good deal — buy now</div>
                  <div className="score-desc">Price is in the bottom 28% historically</div>
                </div>
              </div>

              {/* Best Time To Buy */}
              <div className="card">
                <span className="card-header">Best Time To Buy</span>
                <div className="time-filters">
                  <button className="time-pill active">2–3 days</button>
                  <button className="time-pill">1 week</button>
                  <button className="time-pill">1 month</button>
                </div>
                <div className="prediction-box">
                  <div className="pred-title">↓ Likely to drop slightly</div>
                  <div className="pred-desc">Based on 6-month seasonal pattern</div>
                </div>
              </div>

              {/* Set Price Alert */}
              <div className="card">
                <span className="card-header">
                  Set Price Alert
                </span>
                <div className="alert-form">
                  <div className="input-group">
                    <span>{currencySymbol}</span>
                    <input type="number" value={targetPrice} onChange={(e) => setTargetPrice(parseFloat(e.target.value))} />
                  </div>
                  <button className="btn-outline" 
                    onClick={userLoggedInFlag ? () => handlePriceAlert(targetPrice) : handleLogin}>
                   {userLoggedInFlag ? "🔔 Alert me at this price" : "👤 Log In and Set Price Alert"}
                  </button>
                </div>
              </div>

              {/* Buy Button */}
              {displayUrl && (
                <button 
                  className="btn-buy" 
                  onClick={() => window.open(displayUrl, "_blank", "noopener noreferrer")}
                >
                  Buy on Amazon →
                </button>
              )}

            </div>
          </>
        )}
      </div>  
    
      <LoginModal 
        isOpen={isLoginModalOpen} 
        url={prod_url}
        onClose={() => setLoginModalOpen(false)} 
        /> 
    </>
  );
}
