import { useState } from "react";
import { supabase } from "../utils/supabase"

export default function LoginModal({ isOpen, url, onClose }: {isOpen: boolean, url: string, onClose: () => void}) {
    const [email, setEmail] = useState("");
    const [received, setReceived] = useState<boolean>(false);
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [error, setError] = useState("");


    if (!isOpen) return null;

    const handleMagicLink = async() => {
        if (!email || !email.includes("@")) {
            setError("Please enter a valid email address");
            console.info("Please enter a valid email address");
            return;
        }

        setSubmitting(true);
         
        const { data, error } = await supabase.auth.signInWithOtp({
            email: email,
            options: {
            // I want users to be signed up
            shouldCreateUser: true,
            emailRedirectTo: window.location.origin + window.location.pathname,
            },
        });

        if (error) {
            setError(error.message);
            setSubmitting(false);
        }
        else {
            console.log(`Magic link sent to email = ${email}`);
            setSubmitting(false);
            setReceived(true);
        }


    }

    const handleGoogleOAuth = async() => {

        setSubmitting(true);

        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `http://localhost:3000/products?url=${url}`,
            }       
            })
        if (error) {
            setSubmitting(false);
            setError(error.message);
        }

        else {
            console.log("Google OAuth Ran successfully!! = redirecting to google")
            setSubmitting(false);
            onClose();
        }
    }

    return (
        <>
            <style>{`
            /* The dark semi-transparent background */
            .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.75); /* Slightly darker for dark mode */
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            }

            /* The dark popup box */
            .modal-content {
            background: #1a1a1a; /* Dark gray/black background */
            color: #e8e8e8; /* Light gray text */
            padding: 32px;
            border-radius: 12px;
            width: 90%;
            max-width: 400px;
            position: relative;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            border: 1px solid #2a2a2a; /* Subtle border for depth */
            }

            .close-btn {
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #888;
            transition: color 0.2s;
            }

            .close-btn:hover {
            color: #fff;
            }

            .modal-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 24px;
            }

            /* Darker icon circle with a bright accent */
            .icon-circle {
            width: 50px;
            height: 50px;
            background-color: rgba(99, 102, 241, 0.15); /* Transparent indigo */
            color: #818cf8; /* Light indigo */
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            }

            .modal-header h2 {
            font-size: 1.5rem;
            margin: 0 0 8px 0;
            color: #f9fafb; /* Off-white */
            }

            .modal-header p {
            color: #9ca3af; /* Medium gray */
            margin: 0;
            font-size: 0.9rem;
            }

            /* Dark Google Button */
            .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            padding: 12px;
            border: 1px solid #444;
            border-radius: 8px;
            background: #222;
            color: #e8e8e8;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            }

            .google-btn:hover {
            background-color: #2a2a2a;
            border-color: #555;
            }

            .divider {
            margin: 24px 0;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            }

            .divider::before, .divider::after {
            content: "";
            flex: 1;
            height: 1px;
            background: #333; /* Dark divider lines */
            }

            .divider span {
            padding: 0 12px;
            color: #888;
            font-size: 0.85rem;
            }

            .otp-section {
            display: flex;
            flex-direction: column;
            gap: 16px;
            }

            .otp-label {
            text-align: left;
            margin: 0;
            font-size: 0.9rem;
            color: #d1d5db; /* Light gray */
            font-weight: 500;
            }

            /* Dark Input Field */
            .email-input {
            padding: 12px 16px;
            border: 1px solid #444;
            border-radius: 8px;
            font-size: 1rem;
            color: #fff;
            background: #111; /* Extremely dark inner background */
            width: 100%;
            box-sizing: border-box;
            }

            .email-input::placeholder {
            color: #666;
            }

            .email-input:focus {
            outline: none;
            border-color: #6366f1; /* Indigo focus ring */
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
            }

            .magic-link-btn {
            background: #4f46e5; /* Indigo */
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.2s;
            }

            .magic-link-btn:hover {
            background: #6366f1; /* Brighter indigo on hover */
            }`}
            </style>
            <div className="modal-overlay">
                <div className="modal-content">
                    {/* Close Button */}
                    <button className="close-btn" onClick={onClose}>
                    &times;
                    </button>

                    <div className="modal-header">
                    <div className="icon-circle">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </div>
                    <h2>Login to Continue</h2>
                    <p>Sign in to set price alerts and never miss out on price drops!</p>
                    </div>

                   {received ? (
                    <div className="success-message" style={{ color: "#4ade80", padding: "20px 0" }}>
                        <h3>Check your email!</h3>
                        <p>We sent a magic link to <strong>{email}</strong>. Click the link to instantly log in.</p>
                    </div>
                    ) : (
                    <>
                        {/* Google Login */}
                        <button className="google-btn" onClick={() => handleGoogleOAuth()} disabled={submitting} style={{ opacity: submitting ? 0.7 : 1 }}>
                            {/* Inline Google SVG Logo */}
                        <svg viewBox="0 0 48 48" width="20" height="20">
                            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
                            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
                            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
                            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
                            <path fill="none" d="M0 0h48v48H0z"></path>
                        </svg>
                        Continue with Google
                        </button>

                        <div className="divider">
                        <span>Or</span>
                        </div>

                        {/* Email OTP Login */}
                        <div className="otp-section">
                        <p className="otp-label">Continue via Magic Link</p>
                        <input 
                            type="email" 
                            placeholder="Enter Email" 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="email-input"
                        />
                        {error && <p style={{ color: "#ef4444", fontSize: "0.85rem", margin: "0" }}>{error}</p>}
                        <button className="magic-link-btn" onClick={() => handleMagicLink()} disabled={submitting} style={{ opacity: submitting ? 0.7 : 1 }}>
                            Send Magic Link
                        </button>
                        </div>
                    </>
                    )}
                </div>
            </div>
        </>
    )
}