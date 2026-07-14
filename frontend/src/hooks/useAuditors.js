import { useState, useEffect, useCallback } from "react";
import * as auditorService from "../services/auditor";

export default function useAuditors(showToast) {
  const [auditors, setAuditors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const fetchAuditors = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (searchQuery.trim()) {
        params.search = searchQuery;
      }
      if (statusFilter) {
        params.status = statusFilter;
      }
      const response = await auditorService.getAuditors(params);
      setAuditors(response?.data || []);
    } catch (err) {
      console.error(err);
      setError(err);
      showToast?.(err.message || "Failed to load auditor directory", "error");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, statusFilter, showToast]);

  // Refetch when search query or status filter changes
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchAuditors();
    }, 300); // 300ms debounce for search query input
    return () => clearTimeout(handler);
  }, [searchQuery, statusFilter, fetchAuditors]);

  const createAuditor = async (data) => {
    const tempId = `temp-${Date.now()}`;
    const optimisticAuditor = {
      id: tempId,
      name: data.name,
      email: data.email || "",
      phone: data.phone || "",
      designation: data.designation || "",
      status: data.status || "ACTIVE",
      key_version: 1,
      isOptimistic: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Optimistic append
    setAuditors((prev) => [...prev, optimisticAuditor]);

    try {
      const response = await auditorService.createAuditor(data);
      const newAuditor = response?.data;
      if (newAuditor) {
        const formattedAuditor = {
          id: newAuditor.auditor_id || newAuditor.id,
          name: newAuditor.name,
          email: newAuditor.email,
          phone: newAuditor.phone,
          designation: newAuditor.designation,
          status: newAuditor.status || "ACTIVE",
          key_version: newAuditor.key_version || 1,
          public_key: newAuditor.public_key,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setAuditors((prev) =>
          prev.map((aud) => (aud.id === tempId ? formattedAuditor : aud))
        );
        showToast?.(`Auditor ${data.name} created successfully!`, "success");
        return response; // Return response containing keys and temp password
      }
    } catch (err) {
      // Rollback
      setAuditors((prev) => prev.filter((aud) => aud.id !== tempId));
      showToast?.(err.message || "Failed to register new auditor", "error");
      throw err;
    }
  };

  const updateAuditor = async (id, data) => {
    const previousAuditors = [...auditors];

    // Optimistic update
    setAuditors((prev) =>
      prev.map((aud) => (aud.id === id ? { ...aud, ...data } : aud))
    );

    try {
      const response = await auditorService.updateAuditor(id, data);
      showToast?.("Auditor profile updated", "success");
      return response;
    } catch (err) {
      // Rollback
      setAuditors(previousAuditors);
      showToast?.(err.message || "Failed to update auditor profile", "error");
      throw err;
    }
  };

  const deleteAuditor = async (id) => {
    const previousAuditors = [...auditors];
    const targetAuditor = auditors.find((aud) => aud.id === id);

    // Optimistic delete
    setAuditors((prev) => prev.filter((aud) => aud.id !== id));

    try {
      await auditorService.deleteAuditor(id);
      showToast?.(`Auditor ${targetAuditor?.name || ""} deleted successfully`, "success");
    } catch (err) {
      // Rollback
      setAuditors(previousAuditors);
      showToast?.(err.message || "Failed to delete auditor", "error");
      throw err;
    }
  };

  const rotateKeys = async (id) => {
    const previousAuditors = [...auditors];
    
    // Optimistic update (increment key version)
    setAuditors((prev) =>
      prev.map((aud) =>
        aud.id === id ? { ...aud, key_version: (aud.key_version || 1) + 1 } : aud
      )
    );

    try {
      const response = await auditorService.rotateKeys(id);
      showToast?.("Auditor key pair rotated successfully", "success");
      
      const rotatedData = response?.data;
      if (rotatedData) {
        setAuditors((prev) =>
          prev.map((aud) =>
            aud.id === id
              ? {
                  ...aud,
                  key_version: rotatedData.new_key_version || rotatedData.key_version,
                  public_key: rotatedData.new_public_key || aud.public_key,
                }
              : aud
          )
        );
      }
      return response; // Contains new private key to display to user
    } catch (err) {
      // Rollback
      setAuditors(previousAuditors);
      showToast?.(err.message || "Failed to rotate key pair", "error");
      throw err;
    }
  };

  const downloadCredentials = async (id, name) => {
    try {
      const blobData = await auditorService.downloadCredentials(id);
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `SecureMatch_Auditor_${name}_Credentials.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      showToast?.("Credentials PDF downloaded successfully", "success");
    } catch (err) {
      console.error(err);
      showToast?.("Failed to download credentials PDF", "error");
    }
  };

  return {
    auditors,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    refresh: fetchAuditors,
    createAuditor,
    updateAuditor,
    deleteAuditor,
    rotateKeys,
    downloadCredentials,
  };
}
