"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

interface User {
  id: string;
  phone_number: string;
  username?: string;
  created_at: string;
  owned_agent_ids: string[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loginWithOtp: (phoneNumber: string, code: string) => Promise<void>;
  sendOtp: (phoneNumber: string) => Promise<{ debug_code?: string }>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Default API URL (should match the one in useRegistry)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("agentmesh_token");
      if (token) {
        try {
          // Verify token and get user profile
          const response = await axios.get(`${API_BASE}/users/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data.data.user);
        } catch (error) {
          console.error("Token verification failed:", error);
          localStorage.removeItem("agentmesh_token");
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const sendOtp = async (phoneNumber: string) => {
    const response = await axios.post(`${API_BASE}/auth/send-otp`, {
      phone_number: phoneNumber
    });
    return response.data.data;
  };

  const loginWithOtp = async (phoneNumber: string, code: string) => {
    const response = await axios.post(`${API_BASE}/auth/login`, {
      phone_number: phoneNumber,
      code: code
    });
    
    const { token, user } = response.data.data;
    localStorage.setItem("agentmesh_token", token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("agentmesh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated: !!user,
      loginWithOtp, 
      sendOtp, 
      logout,
      isLoading 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
