"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

type AuthState = "loading" | "signedOut" | "signedIn";

export const App = () => {
  const [auth, setAuth] = useState<AuthState>("loading");

  useEffect(() => {
    fetch("/api/me").then((response) =>
      setAuth(response.ok ? "signedIn" : "signedOut")
    );
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (response.ok) {
      setAuth("signedIn");
    }
    return response.ok;
  };

  const handleLogout = async () => {
    await fetch("/api/logout", { method: "POST" });
    setAuth("signedOut");
  };

  if (auth === "loading") {
    return null;
  }
  if (auth === "signedOut") {
    return <LoginForm onLogin={handleLogin} />;
  }
  return <KanbanBoard onLogout={handleLogout} />;
};
