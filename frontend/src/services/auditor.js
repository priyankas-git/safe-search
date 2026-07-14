import api from "./api";
import { handleApiError } from "../utils/errorHandler";

function isNotFoundError(err) {
  return err?.response?.status === 404;
}

function normalizeAuditorListPayload(response, params = {}) {
  const auditors = response?.data?.data?.auditors || response?.data?.data || [];
  const searchTerm = params.search?.toLowerCase().trim();
  const statusFilter = params.status;

  const filtered = auditors.filter((auditor) => {
    const matchesSearch = !searchTerm || [
      auditor.name,
      auditor.email,
      auditor.designation,
      auditor.phone,
    ].some((value) => (value || "").toLowerCase().includes(searchTerm));

    const matchesStatus = !statusFilter || auditor.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return {
    ...response?.data,
    data: filtered,
  };
}

export async function getAuditors(params = {}) {
  try {
    const res = await api.get("/api/auditors/", { params });
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.get("/api/metrics/internal/");
        return normalizeAuditorListPayload(fallbackRes, params);
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function getAuditor(id) {
  try {
    const res = await api.get(`/api/auditors/${id}/`);
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.get(`/api/auditor/${id}/`);
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function createAuditor(data) {
  try {
    const res = await api.post("/api/auditors/", data);
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.post("/api/auditor/create/", data);
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function updateAuditor(id, data) {
  try {
    const res = await api.patch(`/api/auditors/${id}/`, data);
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const keys = Object.keys(data || {});
        const isStatusOnly = keys.length === 1 && keys[0] === "status";
        const fallbackUrl = isStatusOnly
          ? `/api/auditor/${id}/status/`
          : `/api/auditor/${id}/update/`;
        const fallbackRes = await api.patch(fallbackUrl, data);
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function deleteAuditor(id) {
  try {
    const res = await api.delete(`/api/auditors/${id}/`);
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.delete(`/api/auditor/${id}/delete/`);
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function rotateKeys(id) {
  try {
    const res = await api.post(`/api/auditors/${id}/rotate-key/`);
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.post("/api/auditor/rotate-key/", {
          auditor_id: id,
        });
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}

export async function downloadCredentials(id) {
  try {
    const res = await api.get(`/api/auditors/${id}/credentials/`, {
      responseType: "blob",
    });
    return res.data;
  } catch (err) {
    if (isNotFoundError(err)) {
      try {
        const fallbackRes = await api.get(`/api/auditor/${id}/download/`, {
          responseType: "blob",
        });
        return fallbackRes.data;
      } catch (fallbackErr) {
        throw handleApiError(fallbackErr);
      }
    }
    throw handleApiError(err);
  }
}
