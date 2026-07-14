import React from "react";
import { useAuth } from "../context/AuthContext";
import { hasAnyRole } from "../config/permissions";
import { Spinner } from "../components/Loader";

export default function RoleRoute({ children, allowedRoles, fallback = null }) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-55/40">
        <Spinner text="Verifying access credentials..." />
      </div>
    );
  }

  if (!isAuthenticated || !hasAnyRole(user, allowedRoles)) {
    return fallback;
  }

  return children;
}
