import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  // Separate string states so no object ever reaches JSX
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await api.register(email.trim(), password);
        setSuccessMessage("Account created successfully! Please sign in with your credentials.");
        setIsRegister(false);
        setPassword("");
      } else {
        await api.login(email.trim(), password);
        navigate("/");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected network error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-stone-100">
      <div className="w-full max-w-md bg-white rounded-xl shadow-md border border-stone-200 p-8 space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-black tracking-tight text-emerald-800">
            CropRisk
          </h1>
          <p className="text-xs text-stone-500 font-medium">
            Crop- and Growth-Stage-Aware Agronomic Risk Engine
          </p>
        </div>

        <div className="flex border-b border-stone-200">
          <button
            type="button"
            onClick={() => {
              setIsRegister(false);
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
            className={`flex-1 py-2.5 text-sm font-semibold border-b-2 text-center transition ${
              !isRegister
                ? "border-emerald-700 text-emerald-800"
                : "border-transparent text-stone-400 hover:text-stone-700"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true);
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
            className={`flex-1 py-2.5 text-sm font-semibold border-b-2 text-center transition ${
              isRegister
                ? "border-emerald-700 text-emerald-800"
                : "border-transparent text-stone-400 hover:text-stone-700"
            }`}
          >
            Register
          </button>
        </div>

        {successMessage && (
          <div className="p-3 text-xs bg-emerald-50 text-emerald-800 border border-emerald-300 rounded-md font-medium">
            {successMessage}
          </div>
        )}

        {errorMessage && (
          <div className="p-3 text-xs bg-rose-50 text-rose-800 border border-rose-300 rounded-md font-medium">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="grower@example.com"
              required
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
              Password (min. 8 characters)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded-md shadow transition disabled:opacity-50"
          >
            {loading ? "Processing..." : isRegister ? "Create Grower Account" : "Sign In to Dashboard"}
          </button>
        </form>
      </div>
    </div>
  );
};
