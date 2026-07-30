import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../utils/supabase";
import type { Session } from "@supabase/supabase-js";


export default function NavBar({ onLoginClick }: { onLoginClick: () => void }) {
  const [session, setSession] = useState<Session | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
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
    if (!session) {
        setLoginModalOpen(true);
    }    
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    setDropdownOpen(false);
  }

    return (
        <nav className="nav">
            <div className="logo">
            <span className="logo-icon">◆</span>
            FaroBuy
            </div>

            {session ? (
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
            )}  
        </nav>

    )

}