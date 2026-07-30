"use client"
import Image from "next/image";
import { cache, useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "./utils/supabase";
import { Session } from "@supabase/supabase-js";
import LoginModal from "./components/login_modal";
import NavBar from "./components/nav_bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Home() {
  const [query, setQuery] = useState("");
  const router = useRouter();
  const cacheKey = `search_${query}`;
  const [urlError, setUrlError] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);


  async function handleSearch() {
    if (!query.trim()) return;
    console.log("Searching:", query);
    // Send the query to your local Next.js API route
    const res = await fetch(`/api/search_query?q=${encodeURIComponent(query)}`);
    // Parse the response
    const data = await res.json();
    console.log("Response from fastapi:", data);
    if (data.status === "error") {
      console.error("Received following error when fetching data from database", data.details)
      // setError(data.details);
      return;
    }

    if (data.status === "no_db" && data["url-type"] === "product") {
      console.log(data.details);
      const res_scrape_prod = await fetch(`/api/scrape_product?url=${encodeURIComponent(query)}`)
      const data_scrape_prod = await res_scrape_prod.json();
      if (data_scrape_prod.status === "error") {
        console.error("Received following error when scraping product info:", data_scrape_prod.details)
        return; 
      }
      sessionStorage.setItem("productData", JSON.stringify(data_scrape_prod.content));
      router.push(`/products?url=${encodeURIComponent(query)}`);
      return;
    }


    if (data.status === "no_db" && data["url-type"] === "search") {
      console.log(data.details);
      sessionStorage.removeItem(cacheKey);
      router.push(`/search?q=${encodeURIComponent(query)}`)
      return;
    }

    if (data["url-type"] === "search") {
      sessionStorage.removeItem(cacheKey);
      sessionStorage.setItem("searchResultsDB", JSON.stringify(data.content));
      router.push(`/search?q=${encodeURIComponent(query)}`);
    } else if (data["url-type"] === "product") {
      sessionStorage.setItem("productData", JSON.stringify(data.content));
      router.push(`/products?url=${encodeURIComponent(query)}`);
    }

  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSearch();
  }

  function validateInput(value: string): boolean {
    const looksLikeUrl = /^(www\.|http|ftp|amazon\.|walmart\.|target\.)/i.test(value.trim());

    if (!looksLikeUrl) {
    setUrlError(null);
    return true; // plain text search — always valid
    }

    const validUrl = /^https?:\/\/.+/i.test(value.trim());

    if (!validUrl) {
      setUrlError("Please enter a valid URL starting with https://");
      return false;
    }
    
    setUrlError(null);
    return true;
  }

  return (
        <main className="min-h-screen bg-slate-950 text-slate-50 selection:bg-amber-500/30 flex flex-col relative overflow-hidden">
          
          {/* Subtle Enterprise Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] opacity-20 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/40 via-slate-950 to-slate-950"></div>

          <NavBar />
       
      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 pt-24 pb-16 mx-auto w-full max-w-4xl relative z-10">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-amber-500/20 bg-amber-500/10 text-amber-500 text-sm font-semibold tracking-wide uppercase mb-8 shadow-[0_0_15px_rgba(245,158,11,0.1)]">
          <Anchor className="w-4 h-4" />
          Real prices. No manipulation.
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
          Navigate your way to <br className="hidden md:block" />
          <span className="bg-gradient-to-br from-amber-300 via-amber-500 to-amber-600 bg-clip-text text-transparent">
            the true price.
          </span>
        </h1>



        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 font-medium">
          Paste any Amazon, Walmart, or Target link — or search by name — 
          to cut through the fog and see the complete price history.
        </p>

        {/* Search */}
        <div className="w-full max-w-2xl flex flex-col items-start relative">
          <div className={`relative w-full flex items-center transition-all duration-300 rounded-2xl bg-slate-900/50 border backdrop-blur-sm ${urlError ? 'border-red-500/50 shadow-[0_0_0_3px_rgba(239,68,68,0.1)]' : 'border-slate-800 focus-within:border-amber-500/50 focus-within:shadow-[0_0_0_4px_rgba(245,158,11,0.1)] focus-within:bg-slate-900/80'}`}>

            <Search className="absolute left-4 w-5 h-5 text-slate-500" />

            <Input
              className="h-16 w-full pl-12 pr-[140px] text-lg bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-slate-500 text-slate-50"
              type="text"
              placeholder="Search a product or paste a URL…"
              value={query}
              onChange={(e) => { setQuery(e.target.value); validateInput(e.target.value); }}
              onKeyDown={handleKeyDown}
              autoComplete="off"
              spellCheck={false}
            />

            {query && (
              <button
                onClick={() => { setQuery(""); setUrlError(null); }}
                className="absolute right-[145px] text-slate-500 hover:text-slate-300 transition-colors p-1"
                aria-label="Clear search"
              >
                <X className="w-5 h-5" />
              </button>
            )}

            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <Button 
                onClick={handleSearch}
                disabled={!query.trim() || !!urlError || isLoading}
                className="h-12 px-6 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-base shadow-lg transition-all"
              >
                {isLoading ? "Searching..." : "Illuminate"}
                {!isLoading && <ArrowRight className="w-4 h-4 ml-2 opacity-80" />}
              </Button>
            </div>

            
           
          <button
            className="search-btn"
            onClick={handleSearch}
            disabled={!query.trim() || !!urlError}
          >
            Check Price
          </button>

        </div>
            {/* Validation Error */}
          {urlError && (
            <div className="flex items-center gap-2 mt-3 ml-4 text-red-400 text-sm font-medium">
              <AlertCircle className="w-4 h-4" />
              {urlError}
            </div>
          )}
      </div>
      </section>


      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .root {
          min-height: 100vh;
          /* Midnight Ocean Background */
          background: radial-gradient(circle at top center, #111A31 0%, #0B1121 100%);
          color: #F8FAFC;
          font-family: 'Outfit', 'Inter', system-ui, sans-serif;
          display: flex;
          flex-direction: column;
        }
        /* Nav */


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
          gap: 8px;
          background: rgba(255, 184, 0, 0.1);
          border: 1px solid rgba(255, 184, 0, 0.2);
          color: #FFB800;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          padding: 6px 16px;
          border-radius: 100px;
          margin-bottom: 32px;
          box-shadow: 0 0 20px rgba(255, 184, 0, 0.05);
        }
        
        .eyebrow-icon {
          font-size: 14px;
        }

        .headline {
          font-size: clamp(40px, 7vw, 76px);
          font-weight: 800;
          line-height: 1.1;
          letter-spacing: -2px;
          color: #FFFFFF;
          margin-bottom: 24px;
        }

        /* The Lighthouse Beam Gradient */
        .headline-accent {
          color: transparent;
          background: linear-gradient(135deg, #FFD166 0%, #FFB800 50%, #FF8A00 100%);
          -webkit-background-clip: text;
          background-clip: text;
        }

        .subhead {
          font-size: 17px;
          line-height: 1.6;
          color: #94A3B8;
          max-width: 540px;
          margin-bottom: 48px;
          font-weight: 400;
        }

        /* Search */
        
        
        .search-container {
          width: 100%;
          max-width: 660px;
          display: flex;
          flex-direction: column;
        }

        .search-wrap {
          width: 100%;
          display: flex;
          gap: 10px;
          background: rgba(255, 255, 255, 0.03);
          border: 1.5px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          padding: 8px 8px 8px 12px;
          transition: all 0.3s ease;
        }

        .search-wrap--focused {
          border-color: rgba(255, 184, 0, 0.5);
          background: rgba(255, 255, 255, 0.05);
          box-shadow: 0 0 0 4px rgba(255, 184, 0, 0.1), 0 10px 40px -10px rgba(255, 184, 0, 0.15);
        }

        .search-inner {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 0 8px;
          min-width: 0;
        }

        .search-icon {
          width: 20px;
          height: 20px;
          color: #64748B;
          flex-shrink: 0;
          transition: color 0.3s ease;
        }

        .search-wrap--focused .search-icon {
          color: #FFB800;
        }
         
        .search-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          font-size: 16px;
          color: #F8FAFC;
          min-width: 0;
          font-family: inherit;
        }
        
        .search-input::placeholder { 
          color: #64748B; 
        }

        .search-error {
          font-size: 13px;
          color: #EF4444;
          margin: 10px 0 0 16px;
          text-align: left;
          font-weight: 500;
        }

        .search-wrap--error {
          border-color: rgba(239, 68, 68, 0.5);
          box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
        }

        .clear-btn {
          background: rgba(255,255,255,0.05);
          border: none;
          color: #94A3B8;
          cursor: pointer;
          font-size: 12px;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
          flex-shrink: 0;
        }
        
        .clear-btn:hover { 
          background: rgba(255,255,255,0.1);
          color: #F8FAFC; 
        }


        .search-btn {
          background: linear-gradient(135deg, #FFB800 0%, #FF8A00 100%);
          color: #0F172A;
          border: none;
          border-radius: 12px;
          padding: 14px 28px;
          font-size: 15px;
          font-weight: 700;
          cursor: pointer;
          white-space: nowrap;
          flex-shrink: 0;
          transition: all 0.2s ease;
          font-family: inherit;
          box-shadow: 0 4px 15px rgba(255, 138, 0, 0.2);
        }
        
        .search-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(255, 138, 0, 0.3);
        }
        
        .search-btn:active:not(:disabled) { 
          transform: translateY(0); 
        }
        
        .search-btn:disabled {
          background: #1E293B;
          color: #475569;
          box-shadow: none;
          cursor: not-allowed;
        }

        /* ── Responsive ── */
        @media (max-width: 600px) {
          .hero { padding: 60px 20px 36px; }
          .search-wrap { flex-direction: column; gap: 8px; padding: 10px; }
          .search-inner { padding: 8px 4px; }
          .search-btn { width: 100%; justify-content: center; padding: 16px; }
        }
      `}</style>
    </main>
  );
}
