"use Client"
import { useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "../utils/supabase";
import type { Session } from "@supabase/supabase-js";
import LoginModal from "./login_modal";


export default function NavBar() {
  const [session, setSession] = useState<Session | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const pathname = usePathname();  // retreives the current url path
  const [isLoginModalOpen, setLoginModalOpen] = useState<boolean>(false);


  useEffect(() => {
    // get the current login status - check whether user is logged in or not
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    //  Keep watch for user login/logout
    const { data: listener } = supabase.auth.onAuthStateChange((_e, session) => setSession(session));
    // Stop watching once page is removed
    return () => listener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
       // function checks if user clicked outside the dropdown - if yes then close the dropdown else keep it open
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);  // event listener listens for mouse click, if clicked then fires the function 
    return () => document.removeEventListener("mousedown", handleClickOutside);  // when page is removed, remove the listener
  }, []);

   async function handleLogin() {
    if (!session) { // if the user has not logged in
        setLoginModalOpen(true);
    }    
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    setDropdownOpen(false);
  }

  const isProductPage = pathname?.startsWith("/products");
  const isSearchPage = pathname?.startsWith("/search");

    return (
        <nav className="nav">
            <div className="nav-left">
                {isSearchPage ? (
                  <button className="nav-back-btn" onClick={() => router.push("/")}>
                      ⬅️ Back to Home
                  </button>
                ) : isProductPage ? (
                    <button className="nav-back-btn" onClick={() => router.back()}>
                      ⬅️ Back
                    </button>
                ) : (
                  <div className="logo">
                    <span className="logo-icon">🚨</span>
                    FaroBuy
                  </div>
                )} 
            </div>

            <div className="nav-middle">
                {isProductPage && <span className="nav-title">Product Lens</span>}
            </div>
            
            <div className="nav-right">
              { session ? (
                  <div className="profile-wrap" ref={dropdownRef}>
                    <button
                      className="profile-btn"
                      onClick={() => setDropdownOpen((o) => !o)}
                      aria-label="Account menu"
                    >
                      {session.user.email?.[0]?.toUpperCase() ?? "?"}
                    </button>
                    {dropdownOpen && (
                      <div className="profile-dropdown">
                        <div className="dropdown-email">{session.user.email}</div>
                        <button className="dropdown-item" onClick={() => router.push("/tracked")}>
                          Price Alerts
                        </button>
                        <button className="dropdown-item dropdown-item--danger" onClick={handleLogout}>
                          Log out
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <button className="nav-cta" onClick={handleLogin}>
                    Log in
                  </button>
                )
              }
            </div>


            <LoginModal 
              isOpen = {isLoginModalOpen}
              onClose={() => setLoginModalOpen(false)}
                />

            <style>{`
                /* ── Core Nav Layout (Added to fix visibility) ── */
              .nav {
                display: grid;
                grid-template-columns: 1fr auto 1fr; /* Ensures perfect center alignment for the middle section */
                align-items: center;
                padding: 20px 40px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                width: 100%;
                box-sizing: border-box;
                background: #0a0a0f; /* Match your app background */
                z-index: 100;
              }

              .nav-left {
                justify-self: start;
                display: flex;
                align-items: center;
              }

              .nav-middle {
                justify-self: center;
              }

              .nav-right {
                justify-self: end;
              }

              /* ── Dynamic Elements ── */
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

              .nav-back-btn {
                background: transparent;
                border: none;
                color: #9090a8;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: color 0.15s;
                padding: 0;
              }
              
              .nav-back-btn:hover {
                color: #e8e8f0;
              }

              .nav-title {
                font-size: 16px;
                font-weight: 600;
                color: #fff;
                letter-spacing: 0.5px;
              }

              /* ── Original Buttons & Dropdowns ── */
              .nav-cta {
                background: linear-gradient(135deg, #7c6bff, #9f6bff);
                color: #fff !important;
                border: none;
                font-family: inherit;
                cursor: pointer;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 8px;
              }

              .profile-wrap {
                position: relative;
              }

              .profile-btn {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: linear-gradient(135deg, #7c6bff, #b06bff);
                color: #fff;
                border: none;
                font-weight: 700;
                font-size: 14px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
              }

              .profile-dropdown {
                position: absolute;
                top: 46px;
                right: 0;
                background: #14141c;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 6px;
                min-width: 200px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
                z-index: 20;
              }

              .dropdown-email {
                font-size: 12px;
                color: #6e6e88;
                padding: 8px 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                margin-bottom: 4px;
                word-break: break-all;
              }

              .dropdown-item {
                width: 100%;
                text-align: left;
                background: transparent;
                border: none;
                color: #e8e8f0;
                font-size: 13px;
                padding: 9px 10px;
                border-radius: 8px;
                cursor: pointer;
                font-family: inherit;
              }

              .dropdown-item:hover {
                background: rgba(255, 255, 255, 0.06);
              }

              .dropdown-item--danger {
                color: #e05555;
              }

              /* ── Mobile Responsiveness ── */
              @media (max-width: 600px) {
                .nav { padding: 16px 20px; }
              }
            `}</style>

        </nav>

    )

} 