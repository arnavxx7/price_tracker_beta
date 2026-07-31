"use Client"
import { useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "../utils/supabase";
import type { Session } from "@supabase/supabase-js";
import LoginModal from "./login_modal";
import { Button } from "@/components/ui/button";
import {  DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
 } from "@/components/ui/dropdown-menu";

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
        <nav className="grid grid-cols-3 items-center px-6 py-5 border-b border-white/5 w-full bg-slate-950/80 backdrop-blur-md z-50">
            {/* --- Left section ---- */}
            <div className="justify-self-start flex items-center">
                {isSearchPage ? (
                  <button className="flex items-center gap-2 text-slate-400 hover:text-slate-50 transition-colors text-sm font-medium"
                   onClick={() => router.push("/")}>
                      ⬅️ Back to Home
                  </button>
                ) : isProductPage ? (
                    <button className="flex items-center gap-2 text-slate-400 hover:text-slate-50 transition-colors text-sm font-medium" 
                    onClick={() => router.back()}>
                      ⬅️ Back
                    </button>
                ) : (
                  <div className="flex items-center gap-2 text-lg font-bold tracking-tight text-white">
                    <span className="text-amber-500 text-xl">⚓</span>
                    FaroBuy
                  </div>
                )} 
            </div>
             {/* --- Middle section ---- */}
            <div className="justify-self-center">
                {isProductPage && <span className="text-base font-semibold text-white tracking-wide">Product Lens</span>}
            </div>
             {/* --- Right Section ---- */}
            <div className="justify-self-end">
              { session ? (

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 text-slate-950 border-none font-bold text-sm cursor-pointer flex items-center justify-center hover:shadow-[0_0_15px_rgba(245,158,11,0.3)] transition-all"
                        aria-label="Account menu"
                      >
                        {session.user.email?.[0]?.toUpperCase() ?? "?"}
                      </button>
                    </DropdownMenuTrigger>
                    {/* Shadcn Dropdown Content styled for Midnight theme */}
                    <DropdownMenuContent align="end" className="w-56 bg-slate-900 border-slate-800 text-slate-50 mt-2">
                      <div className="px-2 py-2 text-xs text-slate-400 truncate border-b border-slate-800/80 mb-1">
                        {session.user.email}
                      </div>
                      <DropdownMenuItem 
                        className="cursor-pointer font-medium focus:bg-slate-800 focus:text-slate-50 py-2"
                        onClick={() => router.push("/tracked")}
                      >
                        Price Alerts
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="cursor-pointer font-medium text-red-400 focus:bg-red-500/10 focus:text-red-400 py-2"
                        onClick={handleLogout}
                      >
                        Log out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>    
                
                ) : (
                  <Button 
                    onClick={handleLogin}
                    className="bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-bold hover:from-amber-400 hover:to-amber-500 shadow-md shadow-amber-500/10"
                  >
                    Log in
                  </Button> 
                )
              }
            </div>


            <LoginModal 
              isOpen = {isLoginModalOpen}
              onClose={() => setLoginModalOpen(false)}
                />

        </nav>

    )

} 