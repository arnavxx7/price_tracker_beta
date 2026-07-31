"use client";

// import { fetchExternalImage } from "next/dist/server/image-optimizer";
import { useSearchParams, useRouter } from "next/navigation";
// import { parse } from "path";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import LoginModal from "../components/login_modal";
import NavBar from "../components/nav_bar";
import PriceIntelligence from "../components/price_intelligence";
import { RechartsDevtools } from '@recharts/devtools';
import { supabase } from "../utils/supabase";
import { useEffect, useMemo, useState } from "react";


import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Star, Bell, ExternalLink, LineChart as LineChartIcon } from "lucide-react";


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
  const [priceStats, setPriceStats] = useState({
    lowestPrice: null as number | null,
    highestPrice: null as number | null,
    averagePrice: null as number | null
  })

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

              if (chartData.status === "success") {

                  if (chartData.dp) {
                  setPricePoints(chartData.dp);
                  }

                  if (chartData.stats) {
                    setPriceStats({
                      lowestPrice: chartData.stats.min_price,
                      highestPrice: chartData.stats.max_price,
                      averagePrice: chartData.stats.avg_price,
                    });
                  }
                  
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
  // set placeholder for target price field
  useEffect(() => {
    if (product?.price) {
        setTargetPrice(product.price - 10);
    }
    }, [product]); // runs whenever product changes

  useEffect(() => {
      // track product view
      if (!product?.asin) return;
      const asin = product.asin;

      const trackview = async(asin: string) => {
          const res = await fetch("/api/track/view", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ asin })
          })
          const data = await res.json();

          console.log(`Status of tracking product view: ${data?.status}`)
      };

      trackview(asin);
    }, [product]);

  // Normalise fields — handle both search result shape and product scraper shape
  const displayName = product?.name ?? product?.title ?? null;
  const displayUrl = product?.prod_url ?? product?.url ?? null;
  const displayCountryCode = product?.country_code ?? "com";
  const currencySymbol = product?.currency
    ? (CURRENCY_SYMBOLS[product.currency] ?? product.currency)
    : "";

  // --- DEFINE DERIVED PRICE POSITION ANALYSIS ---
  const priceAnalysis = useMemo(() => {
    const currentPrice = product?.price;
    const { lowestPrice, highestPrice, averagePrice } = priceStats;
    let verdict = "";
    let reason = ""
    let percentile = 0;

    if (currentPrice == null || lowestPrice == null || highestPrice == null || averagePrice == null) {
      verdict = "Insufficient Data";
      reason = "One or more stats is null";
      return {
          verdict: verdict,
          reason: reason,
          percentile: null
      };
    }
    
    if (highestPrice > lowestPrice) {
      percentile = ((currentPrice - lowestPrice) / (highestPrice - lowestPrice)) * 100;
    }

    // Cap the percentile between 0 and 100 (in case the current price is a brand new all-time low or high)
    percentile = Math.max(0, Math.min(100, percentile));

    
    if (percentile < 30) {
      verdict = "Buy Now";
      if (percentile === 0) {
        reason = `Price is at it's all-time lowest!!!`;
      }
      else {
      reason = `Price is in the lowest ${percentile}%`;
      }
    } 
    else if (percentile >= 30 && percentile <= 70) {
      // The Caveat: Check against average price
      if (currentPrice < averagePrice) {
        verdict = "Buy Now";
        reason = "Price is below average";
      } else {
        verdict = "Wait";
        reason = "Expect price to drop in a few weeks";
      }
    } 
    else {
      verdict = "Caution";
      if (percentile === 100) {
        reason = `Price is at it's all-time highest`;
      }
      else {
      reason = `Price is ${percentile-50}% above average`;
      }
    }

    // Return the rounded percentile alongside the verdict so you can feed it to your UI gauge
    return { 
      verdict: verdict, 
      reason: reason, 
      percentile: Math.round(percentile) 
    };
  }, [product, priceStats]);


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

      <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-amber-500/30">
      {/* ── Top Navigation ── */}
       <NavBar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <div className="w-8 h-8 border-4 border-amber-500/20 border-t-amber-500 rounded-full animate-spin mb-4" />
              Fetching product details...
            </div>
          )}

          {error && (
            <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-center max-w-lg mx-auto mt-10">
              {error}
            </div>
          )}


        {!loading && !error && product && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            {/* ── LEFT COLUMN ── */}
            <div className="xl:col-span-8 space-y-6">
              
              {/* Product Hero Card */}
              <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm overflow-hidden">
                <CardContent className="p-6 sm:p-8">
                  <div className="flex flex-col md:flex-row gap-8">
                    {/*  Product Image  */}
                    <div className="w-full md:w-1/3 flex-shrink-0 bg-white rounded-xl p-4 flex items-center justify-center aspect-square">
                      {product.img_url ? (
                        <img src={product.img_url} alt={displayName ?? "Product"} className="object-contain w-full h-full mix-blend-multiply"/>
                      ) : (
                        <span className="text-slate-400 font-medium">No Image</span>
                      )}
                    </div>

                    {/* Product Info  */}
                    <div className="flex flex-col justify-center flex-1">
                      <div className="flex flex-wrap gap-2 mb-3">
                        <Badge variant="outline" className="border-slate-700 text-slate-300">
                            amazon.{displayCountryCode}
                        </Badge>
                        {product.prime && (
                          <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20">
                              ✓ Prime
                            </Badge>
                        )}
                      </div>

                      <h1 className="text-2xl sm:text-3xl font-bold text-white leading-tight mb-4">
                        {displayName ?? "Name unavailable"}
                      </h1>
                      
                      <div className="flex items-end gap-3 mb-4">
                         <span className="text-4xl font-extrabold text-amber-500 tracking-tight">
                          {currencySymbol}{(product.price ?? 0).toLocaleString()}
                         </span>
                         {product.org_price != null && product.price != null && product.org_price > product.price && (
                         <span className="text-lg text-slate-500 line-through mb-1">
                          {currencySymbol}{product.org_price.toLocaleString()}
                         </span>
                         )}
                          {product.discount_percent != null && product.discount_percent > 0 && (
                            <Badge className="mb-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              {product.discount_percent}% off
                            </Badge>
                         )}
                      </div>
                      

                      <div className="flex items-center gap-2 text-sm text-slate-400 font-medium">
                        {product.rating != null && (
                          <div className="flex items-center text-amber-500">
                              <Star className="w-4 h-4 fill-current mr-1" />
                              <span className="text-slate-300">{product.rating}</span>
                            </div>
                        )}
                        <span>·</span>
                        <span className="truncate">{product.brand_name ?? "Unknown Brand"}</span>
                        <span>·</span>
                        <span className="font-mono text-xs text-slate-500">ASIN: {product.asin ?? "N/A"}</span>
                      </div>
                    </div>
                </div>
                </CardContent>
              </Card>

              {/* 2. Shadcn Price History Chart */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-slate-800/50">
                  <CardTitle className="text-lg font-semibold text-white">Price History</CardTitle>
                    <div className="flex bg-slate-950 rounded-lg p-1 border border-slate-800">
                        <button className="px-3 py-1 text-xs font-medium rounded-md bg-slate-800 text-white shadow-sm">1M</button>
                        <button className="px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition-colors">3M</button>
                        <button className="px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition-colors">All</button>
                    </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {price_points.length > 0 ? (
                    <div className="h-[300px] w-full">
                      {/* Shadcn Chart Wrapper */}
                        <ChartContainer 
                          config={{ price: { label: "Price", color: "#FFB800" } }}
                          className="h-full w-full"
                        >
                            <LineChart data={price_points} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                              <XAxis 
                                dataKey="date_yaxis" 
                                stroke="#64748B" 
                                fontSize={12} 
                                tickLine={false} 
                                axisLine={false} 
                              />
                              <YAxis 
                                stroke="#64748B" 
                                fontSize={12} 
                                tickLine={false} 
                                axisLine={false} 
                                tickFormatter={(val) => `${currencySymbol}${val}`} 
                              />
                              <ChartTooltip 
                              content={<ChartTooltipContent indicator="line" />} 
                              cursor={{ stroke: '#334155', strokeWidth: 1 }}
                              />
                              <Line
                                type="stepAfter" // stepAfter is often better for exact price drops
                                dataKey="price"
                                stroke="var(--color-price)"
                                strokeWidth={2.5}
                                dot={false}
                                activeDot={{ r: 6, fill: '#FFB800', stroke: '#0B1121', strokeWidth: 2 }}
                              />
                            </LineChart>
                        </ChartContainer>
                    </div>
                  ): (
                    <div className="h-[300px] flex flex-col items-center justify-center text-slate-500">
                        <LineChartIcon className="w-10 h-10 mb-2 opacity-50" />
                        <p>Chart data unavailable</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 3. Product Details */}
              <div>
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 px-1">
                    Technical Details
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: "Brand", value: product.brand_name ?? "Unavailable" },
                      { label: "Currency", value: product.currency ? `${product.currency} (${currencySymbol})` : "Unavailable" },
                      { label: "ASIN", value: product.asin ?? "Unavailable" },
                      { label: "Marketplace", value: `amazon.${displayCountryCode}` }
                    ].map((item, i) => (
                      <div key={i} className="p-4 rounded-xl bg-slate-900/30 border border-slate-800">
                        <p className="text-xs text-slate-500 mb-1">{item.label}</p>
                        <p className="text-sm font-medium text-slate-200 truncate">{item.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>



              {/* ── RIGHT COLUMN ── */}
            <div className="xl:col-span-4 space-y-6">
                
              {/* Price Intelligence */}
              <PriceIntelligence
                priceAnalysis={priceAnalysis}
                priceStats={priceStats}
                currentPrice={product.price}
                currencySymbol={currencySymbol}
              />

              {/* Set Price Alert */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg font-semibold flex items-center gap-2">
                      <Bell className="w-5 h-5 text-amber-500" />
                      Set Price Alert
                   </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-medium">
                          {currencySymbol}
                        </span>
                        <Input 
                          type="number" 
                          value={targetPrice} 
                          onChange={(e) => setTargetPrice(parseFloat(e.target.value))}
                          className="pl-8 bg-slate-950 border-slate-800 focus-visible:ring-amber-500 text-slate-100"
                        />
                     </div>
                     <Button 
                        variant={userLoggedInFlag ? "default" : "outline"}
                        className={userLoggedInFlag ? "bg-slate-100 text-slate-900 hover:bg-slate-300" : "border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"}
                        onClick={userLoggedInFlag ? () => handlePriceAlert(targetPrice) : handleLogin}
                      >
                        {userLoggedInFlag ? "🔔 Alert me at this price" : "👤 Log In and Set Price Alert"}
                      </Button>
                  </div>
                </CardContent>
              </Card>
              {/* <div className="card">
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
              </div> */}

              {/* Buy Button */}
              {displayUrl && (
                <Button 
                    className="w-full h-14 text-lg font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-[0_0_20px_rgba(245,158,11,0.2)] hover:shadow-[0_0_25px_rgba(245,158,11,0.4)] transition-all"
                    onClick={() => window.open(displayUrl, "_blank", "noopener noreferrer")}
                  >
                    Buy on Amazon
                    <ExternalLink className="w-5 h-5 ml-2 opacity-80" />
                 </Button>
              )}

            </div>
          </div>
        )}
 
    
      <LoginModal 
        isOpen={isLoginModalOpen} 
        onClose={() => setLoginModalOpen(false)} 
        /> 
      </div>
     </div>
    </>
  );
}
