import { useMemo, useState } from "react"

interface PriceAnalysis {
    verdict: string;
    reason: string;
    percentile: number | null;
}

interface PriceStats {
    lowestPrice: number | null;
    highestPrice: number | null;
    averagePrice: number | null;
}

interface PriceIntelligenceProps {
    priceAnalysis: PriceAnalysis;
    priceStats: PriceStats;
    currentPrice: number | null;
    currencySymbol: string;
}

export default function PriceIntelligence({
    priceAnalysis,
    priceStats,
    currentPrice,
    currencySymbol,
}: PriceIntelligenceProps)  {
    const { verdict, reason, percentile } = priceAnalysis;
    const { lowestPrice, highestPrice, averagePrice } = priceStats

    const verdictConfig = {
    "Buy Now": {
      color: "#4caf82",
      bg: "rgba(76,175,130,0.08)",
      border: "rgba(76,175,130,0.2)",
      icon: "↓",
    },
    "Wait": {
      color: "#f5a623",
      bg: "rgba(245,166,35,0.08)",
      border: "rgba(245,166,35,0.2)",
      icon: "→",
    },
    "Caution": {
      color: "#e05555",
      bg: "rgba(224,85,85,0.08)",
      border: "rgba(224,85,85,0.2)",
      icon: "↑",
    },
    "Insufficient Data": {
      color: "#6e6e88",
      bg: "rgba(110,110,136,0.08)",
      border: "rgba(110,110,136,0.2)",
      icon: "?",
        },
    };

    const config = verdictConfig[verdict as keyof typeof verdictConfig];

    const dotPosition = percentile != null ? percentile : null;


    const avgPosition = useMemo(() => {
        const hasValidData = averagePrice != null && lowestPrice != null && highestPrice != null;

        if (!hasValidData) {
            return null;
        }

        if (highestPrice === lowestPrice) {
            return 50;
        }

        const range = highestPrice - lowestPrice;
        const position = ((averagePrice - lowestPrice) / range) * 100;

        return Math.min(100, Math.max(0, position));
    }, [averagePrice, lowestPrice, highestPrice]);


    const hasStats = lowestPrice != null && highestPrice != null;

    const getMessage = (percentile: number) => {
        if (percentile === 0) {
            return 'Lowest price ever recorded for this product';
        }
        else if (percentile === 100) {
            return 'Highest price ever recorded for this product';
        }
        else if (percentile < 30) {
            return `Price in the bottom ${percentile}% of historical range`;
        }

        else if (percentile < 70 && percentile >= 30) {
            return `Price is close to the historical average`;
        }

        else if (percentile > 70) {
            return `Price in the top ${100-percentile}% of historical range`;
        }

        else {
            return `Just do what you fucking want!!!!`
        }
    };

     return (
    <>
      <style>{`
        .pi-panel {
          background: #13131a;
          border: 1px solid #2a2a3a;
          border-radius: 16px;
          overflow: hidden;
        }

        .pi-header {
          padding: 14px 20px;
          border-bottom: 1px solid #2a2a3a;
        }

        .pi-header p {
          margin: 0;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: #3e3e56;
        }

        /* ── Verdict ── */
        .pi-verdict {
          padding: 20px;
          border-bottom: 1px solid #2a2a3a;
        }

        .pi-verdict-inner {
          display: flex;
          align-items: flex-start;
          gap: 14px;
        }

        .pi-verdict-icon {
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          font-weight: 700;
        }

        .pi-verdict-text h3 {
          margin: 0 0 4px;
          font-size: 18px;
          font-weight: 600;
          line-height: 1.2;
        }

        .pi-verdict-text p {
          margin: 0;
          font-size: 12px;
          color: #6e6e88;
          line-height: 1.5;
        }

        .pi-percentile-badge {
          display: inline-block;
          margin-top: 8px;
          font-size: 11px;
          font-weight: 500;
          padding: 3px 10px;
          border-radius: 100px;
        }

        /* ── Price position bar ── */
        .pi-position {
          padding: 15px;
          border-bottom: 1px solid #2a2a3a;
        }

        .pi-position-label {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
        }

        .pi-position-label p {
          margin: 0;
          font-size: 12px;
          font-weight: 500;
          color: #e8e8f0;
        }

        .pi-bar-wrap {
            position: relative;
            margin-bottom: 12px;
            margin-top: 50px;
            margin-left: 18px; 
            margin-right: 18px;
        }

        .pi-bar-track {
          height: 6px;
          border-radius: 3px;
          background: linear-gradient(to right, #4caf82, #f5a623, #e05555);
          position: relative;
        }

        .pi-bar-avg-tick {
          position: absolute;
          top: -4px;
          width: 2px;
          height: 14px;
          background: rgba(255,255,255,0.25);
          border-radius: 1px;
          transform: translateX(-50%);
        }

        .pi-bar-dot {
          position: absolute;
          top: 50%;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #13131a;
          border: 2.5px solid;
          transform: translate(-50%, -50%);
        }

        .pi-bar-callout {
          position: absolute;
          top: -38px;
          transform: translateX(-50%);
          white-space: nowrap;
        }

        .pi-bar-callout-inner {
          border-radius: 6px;
          padding: 3px 8px;
          font-size: 11px;
          font-weight: 600;
        }

        .pi-bar-callout-arrow {
          width: 0;
          height: 0;
          border-left: 4px solid transparent;
          border-right: 4px solid transparent;
          margin: 0 auto;
        }

        .pi-bar-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 10px;
          position: relative;
        }

        .pi-bar-labels div { text-align: center; }
        .pi-bar-labels div:first-child { text-align: left; }
        .pi-bar-labels div:last-child { text-align: right; }

        .pi-bar-avg-label {
          position: absolute;
          transform: translateX(-50%); /* Centers the text exactly underneath the tick */
          text-align: center;
        }

         .lbl {
          display: block;
          font-size: 10px;
          color: #3e3e56;
          margin-bottom: 2px;
        }

        .pi-bar-labels .val {
          display: block;
          font-size: 12px;
          font-weight: 500;
        }

        /* ── Stats ── */
        .pi-stats {
          padding: 16px 20px;
        }

        .pi-stats-label {
          margin: 0 0 10px;
          font-size: 12px;
          font-weight: 500;
          color: #e8e8f0;
        }

        .pi-stats-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
        }

        .pi-stat-card {
          background: #0a0a0f;
          border: 1px solid #2a2a3a;
          border-radius: 10px;
          padding: 10px 8px;
          text-align: center;
        }

        .pi-stat-card .slbl {
          display: block;
          font-size: 10px;
          color: #3e3e56;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 4px;
        }

        .pi-stat-card .sval {
          display: block;
          font-size: 14px;
          font-weight: 600;
        }

        .pi-no-data {
          padding: 20px;
          text-align: center;
          color: #3e3e56;
          font-size: 13px;
        }
      `}</style>

      <div className="pi-panel">
        {/* Header */}
        <div className="pi-header">
          <p>Price Intelligence</p>
        </div>

        {/* Verdict */}
        <div className="pi-verdict">
          <div className="pi-verdict-inner">
            <div
              className="pi-verdict-icon"
              style={{ background: config.bg, border: `1px solid ${config.border}`, color: config.color }}
            >
              {config.icon}
            </div>
            <div className="pi-verdict-text">
              <h3 style={{ color: config.color }}>{verdict}</h3>
              <p>{reason}</p>
              {percentile != null && (
                <span
                  className="pi-percentile-badge"
                  style={{ background: config.bg, border: `1px solid ${config.border}`, color: config.color }}
                >{getMessage(percentile)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Price position bar */}
        {hasStats && dotPosition != null ? (
          <div className="pi-position">
            <div className="pi-position-label">
              <p>Price position</p>
            </div>

            <div className="pi-bar-wrap">
              {/* Callout above dot */}
              {currentPrice != null && (
                <div className="pi-bar-callout" style={{ left: `${dotPosition}%` }}>
                  <div
                    className="pi-bar-callout-inner"
                    style={{ background: config.bg, border: `1px solid ${config.border}`, color: config.color }}
                  >
                    {currencySymbol}{currentPrice.toLocaleString()}
                  </div>
                  <div
                    className="pi-bar-callout-arrow"
                    style={{ borderTop: `4px solid ${config.border}` }}
                  />
                </div>
              )}

              <div className="pi-bar-track">
                {/* Average tick */}
                {avgPosition != null && (
                  <div className="pi-bar-avg-tick" style={{ left: `${avgPosition}%` }} />
                )}
                {/* Current price dot */}
                <div
                  className="pi-bar-dot"
                  style={{ left: `${dotPosition}%`, borderColor: config.color }}
                />
                {avgPosition != null && (
                <div style = {{
                    position: "absolute",
                    top: "18px",                          // below the bar track
                    left: `${avgPosition}%`,
                    transform: "translateX(-50%)",        // center under the tick
                    textAlign: "center",
                    
                }}>
                  <span className="lbl">Avg</span>
                  <span className="val" style={{ color: "#6e6e88", display: "block", fontSize: "12px", fontWeight: 500  }}>
                    {currencySymbol}{averagePrice != null ? Math.round(averagePrice).toLocaleString() : "—"}
                  </span>
                </div>
              )}

              </div>
            </div>

            <div className="pi-bar-labels">
              <div>
                <span className="lbl">Lowest</span>
                <span className="val" style={{ color: "#4caf82" }}>
                  {currencySymbol}{lowestPrice?.toLocaleString()}
                </span>
              </div>

              <div>
                <span className="lbl">Highest</span>
                <span className="val" style={{ color: "#e05555" }}>
                  {currencySymbol}{highestPrice?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="pi-no-data">Not enough price history to show position</div>
        )}

        {/* Stats */}
        {hasStats && (
          <div className="pi-stats">
            <p className="pi-stats-label">Price stats</p>
            <div className="pi-stats-grid">
              <div className="pi-stat-card">
                <span className="slbl">Lowest</span>
                <span className="sval" style={{ color: "#4caf82" }}>
                  {currencySymbol}{lowestPrice?.toLocaleString()}
                </span>
              </div>
              <div className="pi-stat-card">
                <span className="slbl">Average</span>
                <span className="sval" style={{ color: "#e8e8f0" }}>
                  {currencySymbol}{averagePrice != null ? Math.round(averagePrice).toLocaleString() : "—"}
                </span>
              </div>
              <div className="pi-stat-card">
                <span className="slbl">Highest</span>
                <span className="sval" style={{ color: "#e05555" }}>
                  {currencySymbol}{highestPrice?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}