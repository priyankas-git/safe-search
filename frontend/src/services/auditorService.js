import api from "./api";
import { handleApiError } from "../utils/errorHandler";
import * as restfulAuditor from "./auditor";

// Legacy Compatibility API
export async function rotateAuditorKey(auditorId) {
  try {
    const res = await api.post("/api/auditor/rotate-key/", {
      auditor_id: auditorId
    });
    return res.data;
  } catch (err) {
    throw handleApiError(err);
  }
}

export async function getAuditorLogs(auditorId) {
  try {
    const res = await api.get(`/api/auditor/${auditorId}/logs/`);
    return res.data;
  } catch (err) {
    throw handleApiError(err);
  }
}

// Export new RESTful methods as well
export const getAuditors = restfulAuditor.getAuditors;
export const getAuditor = restfulAuditor.getAuditor;
export const createAuditor = restfulAuditor.createAuditor;
export const updateAuditor = restfulAuditor.updateAuditor;
export const deleteAuditor = restfulAuditor.deleteAuditor;
export const rotateKeys = restfulAuditor.rotateKeys;
export const downloadCredentials = restfulAuditor.downloadCredentials;