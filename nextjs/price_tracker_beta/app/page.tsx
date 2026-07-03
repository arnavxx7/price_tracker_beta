"use client"
import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  async function handleSearch() {
    if (!query.trim()) return;
    console.log("Searching:", query);
    // Send the query to your local Next.js API route
    const res = await fetch(`/api/search_query?q=${encodeURIComponent(query)}`);
    // Parse the response
    const data = await res.json();
    console.log("Response from fastapi:", data);
    if (data.status === "error") {
      console.log("Received error when fetching data from url")
      // setError(data.details);
      return;
    }

    if (data["url-type"] === "search") {
      sessionStorage.setItem("searchResults", JSON.stringify(data.content));
      router.push(`/search?q=${encodeURIComponent(query)}`);
    } else if (data["url-type"] === "product") {
      sessionStorage.setItem("productData", JSON.stringify(data.content));
      router.push(`/products?url=${encodeURIComponent(query)}`);
    }

  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSearch();
  }

  return (
        <main className="root">

      {/* Hero */}
      <section className="hero">
        <div className="eyebrow">Real prices. No manipulation.</div>

        <h1 className="headline">
          Track anything and 
          <br />
          <span className="headline-accent">everything!</span>
        </h1>

        <p className="subhead">
          Paste any Amazon, Walmart, Target, Best Buy, or Costco link —
          or search by name — to see the full price history and find out.
        </p>

        {/* Search */}
        <div className={"search-wrap"}>
          <div className="search-inner">
            <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              className="search-input"
              type="text"
              placeholder="Search a product or paste a URL…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button
                className="clear-btn"
                onClick={() => setQuery("")}
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <button
            className="search-btn"
            onClick={handleSearch}
            disabled={!query.trim()}
          >
            Check Price
          </button>
        </div>
      </section>


      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .root {
          min-height: 100vh;
          background: #0a0a0f;
          color: #e8e8f0;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          display: flex;
          flex-direction: column;
        }

        /* Nav */
        .nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 40px;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .logo {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 17px;
          font-weight: 700;
          letter-spacing: -0.3px;
          color: #fff;
        }
        .logo-icon {
          font-size: 20px;
          color: #7c6bff;
        }
        .nav-links {
          display: flex;
          align-items: center;
          gap: 28px;
        }
        .nav-links a {
          color: #9090a8;
          text-decoration: none;
          font-size: 14px;
          font-weight: 500;
          transition: color 0.15s;
        }
        .nav-links a:hover { color: #e8e8f0; }
        .nav-cta {
          background: rgba(124, 107, 255, 0.15);
          color: #a99fff !important;
          padding: 8px 16px;
          border-radius: 8px;
          border: 1px solid rgba(124, 107, 255, 0.3);
          transition: background 0.15s !important;
        }
        .nav-cta:hover {
          background: rgba(124, 107, 255, 0.25) !important;
          color: #c4bcff !important;
        }

        /* Hero */
        .hero {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 80px 24px 48px;
          max-width: 760px;
          margin: 0 auto;
          width: 100%;
        }

        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(124, 107, 255, 0.1);
          border: 1px solid rgba(124, 107, 255, 0.25);
          color: #a99fff;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 6px 14px;
          border-radius: 100px;
          margin-bottom: 32px;
        }

        .headline {
          font-size: clamp(44px, 8vw, 80px);
          font-weight: 800;
          line-height: 1.05;
          letter-spacing: -2.5px;
          color: #ffffff;
          margin-bottom: 20px;
        }
        .headline-accent {
          color: transparent;
          background: linear-gradient(135deg, #7c6bff 0%, #b06bff 50%, #ff6bbb 100%);
          -webkit-background-clip: text;
          background-clip: text;
        }

        .subhead {
          font-size: 16px;
          line-height: 1.65;
          color: #6e6e88;
          max-width: 520px;
          margin-bottom: 44px;
        }

        /* Search */
        .search-wrap {
          width: 100%;
          max-width: 660px;
          display: flex;
          gap: 10px;
          background: rgba(255,255,255,0.04);
          border: 1.5px solid rgba(255,255,255,0.1);
          border-radius: 16px;
          padding: 6px 6px 6px 8px;
          transition: border-color 0.2s, box-shadow 0.2s;
          margin-bottom: 20px;
        }
        .search-wrap--focused {
          border-color: rgba(124, 107, 255, 0.6);
          box-shadow: 0 0 0 3px rgba(124, 107, 255, 0.12);
        }

        .search-inner {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 8px;
          min-width: 0;
        }
        .search-icon {
          width: 18px;
          height: 18px;
          color: #4e4e66;
          flex-shrink: 0;
        }
        .search-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          font-size: 15px;
          color: #e8e8f0;
          min-width: 0;
          font-family: inherit;
        }
        .search-input::placeholder { color: #3e3e56; }

        .clear-btn {
          background: transparent;
          border: none;
          color: #4e4e66;
          cursor: pointer;
          font-size: 12px;
          padding: 2px 4px;
          border-radius: 4px;
          transition: color 0.15s;
          flex-shrink: 0;
        }
        .clear-btn:hover { color: #9090a8; }

        .search-btn {
          background: linear-gradient(135deg, #7c6bff, #9f6bff);
          color: #fff;
          border: none;
          border-radius: 11px;
          padding: 12px 24px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
          flex-shrink: 0;
          transition: opacity 0.15s, transform 0.1s;
          font-family: inherit;
          letter-spacing: -0.1px;
        }
        .search-btn:hover:not(:disabled) {
          opacity: 0.9;
          transform: translateY(-1px);
        }
        .search-btn:active:not(:disabled) { transform: translateY(0); }
        .search-btn:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }

        /* Quick links */
        .quick-links {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: center;
        }
        .quick-label {
          font-size: 12px;
          color: #3e3e56;
          font-weight: 500;
        }
        .quick-chip {
          background: transparent;
          border: 1px solid rgba(255,255,255,0.08);
          color: #5e5e7a;
          font-size: 12px;
          font-weight: 500;
          padding: 5px 12px;
          border-radius: 100px;
          cursor: pointer;
          transition: border-color 0.15s, color 0.15s;
          font-family: inherit;
        }
        .quick-chip:hover {
          border-color: rgba(124, 107, 255, 0.4);
          color: #a99fff;
        }

        /* Stats bar */
        .stats-bar {
          display: flex;
          justify-content: center;
          gap: 0;
          border-top: 1px solid rgba(255,255,255,0.06);
          padding: 28px 24px;
        }
        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 3px;
          padding: 0 48px;
          border-right: 1px solid rgba(255,255,255,0.06);
        }
        .stat:last-child { border-right: none; }
        .stat-value {
          font-size: 22px;
          font-weight: 800;
          letter-spacing: -0.5px;
          color: #fff;
        }
        .stat-label {
          font-size: 11px;
          color: #3e3e56;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        /* Responsive */
        @media (max-width: 600px) {
          .nav { padding: 16px 20px; }
          .nav-links { gap: 16px; }
          .hero { padding: 60px 20px 36px; }
          .search-wrap { flex-direction: column; gap: 8px; padding: 8px; }
          .search-inner { padding: 8px 4px; }
          .search-btn { width: 100%; justify-content: center; padding: 14px; }
          .stat { padding: 0 24px; }
          .stat-value { font-size: 18px; }
        }
      `}</style>
    </main>
  );
}
