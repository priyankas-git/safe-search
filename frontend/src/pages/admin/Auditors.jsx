import React, { useState } from "react";
import CreateAuditorCard from "../../components/CreateAuditorCard";
import useAuditors from "../../hooks/useAuditors";
import { getAuditorLogs } from "../../services/auditorService";
import {
  PageHeader,
  ContentCard,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableCell,
  Button,
  Badge,
  EmptyState,
  Modal,
  SearchInput,
  SelectInput,
  InputGroup,
  FieldLabel,
} from "../../components/ui";
import { Spinner } from "../../components/Loader";

export default function Auditors({ showToast }) {
  const {
    auditors,
    loading,
    createAuditor,
    updateAuditor,
    deleteAuditor,
    rotateKeys,
    downloadCredentials,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
  } = useAuditors(showToast);

  const [selectedAuditor, setSelectedAuditor] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [rotatedKey, setRotatedKey] = useState(null);
  const [rotatedAuditorName, setRotatedAuditorName] = useState("");
  const [copiedKey, setCopiedKey] = useState(false);

  // Timeline Drawer States
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Action states for table items
  const [actionId, setActionId] = useState(null);

  const handleOpenDetails = (auditor) => {
    setSelectedAuditor(auditor);
    setIsDetailsOpen(true);
  };

  const handleToggleStatus = async (auditor) => {
    const nextStatus = auditor.status === "ACTIVE" ? "DISABLED" : "ACTIVE";
    try {
      setActionId(auditor.id);
      await updateAuditor(auditor.id, { status: nextStatus });
    } catch (err) {
      console.error(err);
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (auditor) => {
    if (window.confirm(`Are you sure you want to delete ${auditor.name}? This will also delete their corresponding user login.`)) {
      try {
        setActionId(auditor.id);
        await deleteAuditor(auditor.id);
      } catch (err) {
        console.error(err);
      } finally {
        setActionId(null);
      }
    }
  };

  const handleRotateKey = async (auditor) => {
    if (window.confirm(`Rotate keys for ${auditor.name}? A new key pair will be generated. The private key will be displayed once.`)) {
      try {
        setActionId(auditor.id);
        const res = await rotateKeys(auditor.id);
        const creds = res?.data;
        if (creds?.new_private_key) {
          setRotatedKey(creds.new_private_key);
          setRotatedAuditorName(auditor.name);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setActionId(null);
      }
    }
  };

  const handleCopyRotatedKey = async () => {
    if (rotatedKey) {
      await navigator.clipboard.writeText(rotatedKey);
      setCopiedKey(true);
      showToast?.("Rotated private key copied to clipboard", "success");
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleOpenTimeline = async (auditor) => {
    setSelectedAuditor(auditor);
    setIsDrawerOpen(true);
    setLoadingLogs(true);
    try {
      const res = await getAuditorLogs(auditor.id);
      setLogs(res?.data?.logs || []);
    } catch (err) {
      console.error(err);
      showToast?.("Failed to fetch auditor search logs", "error");
    } finally {
      setLoadingLogs(false);
    }
  };

  const tableHeaders = [
    "Auditor Identity",
    "Contact & Org",
    "Key Info",
    "Status",
    "Actions",
  ];

  return (
    <div className="space-y-6 font-sans">
      <PageHeader
        title="Auditor Management"
        description="Register external authorities, audit public keys, trigger secret rotation, and trace search activities."
      />

      {/* CREATE CARD */}
      <CreateAuditorCard createAuditor={createAuditor} showToast={showToast} />

      {/* FILTER & TABLE */}
      <ContentCard>
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-gray-100 mb-5 gap-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 tracking-tight">Registered Auditors</h2>
            <p className="text-xs text-gray-500 mt-1 font-light">
              Manage credentials, active key versions, and search query authorization logs.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            <SearchInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search auditors..."
              className="max-w-xs"
            />
            <SelectInput
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              options={[
                { value: "", label: "All Statuses" },
                { value: "ACTIVE", label: "Active" },
                { value: "DISABLED", label: "Disabled" },
              ]}
              className="max-w-xs"
            />
          </div>
        </div>

        {loading && auditors.length === 0 ? (
          <div className="py-12 flex items-center justify-center">
            <Spinner text="Loading auditors..." />
          </div>
        ) : auditors.length === 0 ? (
          <EmptyState
            title="No auditors registered"
            description="Register a new auditor organization above to generate public key directories."
            className="border-dashed"
          />
        ) : (
          <Table>
            <TableHeader headers={tableHeaders} />
            <TableBody>
              {auditors.map((auditor) => (
                <TableRow key={auditor.id}>
                  <TableCell isFirst>
                    <div className="cursor-pointer" onClick={() => handleOpenDetails(auditor)}>
                      <p className="text-sm font-semibold text-gray-900 hover:text-blue-600 transition">
                        {auditor.name}
                      </p>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">ID: {auditor.id}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-gray-700">
                    <p className="font-medium text-gray-900">{auditor.designation || "External authority"}</p>
                    <p className="text-xs text-gray-500 font-light mt-0.5">{auditor.email || "No email"}</p>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1 items-start">
                      <Badge variant="blue">
                        Key Version {auditor.key_version || 1}
                      </Badge>
                      <span className="text-3xs text-gray-400 font-mono">
                        {auditor.public_key ? `${auditor.public_key.substring(0, 30)}...` : "No key"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={auditor.status === "ACTIVE" ? "emerald" : "rose"}>
                      {auditor.status === "ACTIVE" ? "Active" : "Disabled"}
                    </Badge>
                  </TableCell>
                  <TableCell isLast>
                    <div className="flex items-center justify-end gap-1.5 flex-wrap">
                      <Button
                        variant="secondary"
                        onClick={() => handleOpenDetails(auditor)}
                        className="px-2 py-1 text-2xs"
                      >
                        Details
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleOpenTimeline(auditor)}
                        className="px-2 py-1 text-2xs text-blue-600"
                      >
                        Logs
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => downloadCredentials(auditor.id, auditor.name)}
                        className="px-2 py-1 text-2xs text-emerald-600"
                      >
                        Credentials
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleRotateKey(auditor)}
                        disabled={actionId === auditor.id}
                        className="px-2 py-1 text-2xs text-amber-600"
                      >
                        Rotate
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleToggleStatus(auditor)}
                        disabled={actionId === auditor.id}
                        className={`px-2 py-1 text-2xs ${auditor.status === "ACTIVE" ? "text-rose-600" : "text-emerald-600"}`}
                      >
                        {auditor.status === "ACTIVE" ? "Disable" : "Enable"}
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleDelete(auditor)}
                        disabled={actionId === auditor.id}
                        className="px-2 py-1 text-2xs text-red-700 bg-red-50 hover:bg-red-100 border-red-200"
                      >
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </ContentCard>

      {/* DETAILS VIEW MODAL */}
      <Modal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        title="🕵️ Auditor Profile & Directory Details"
        className="max-w-xl"
      >
        {selectedAuditor && (
          <div className="space-y-4 font-sans text-sm text-gray-800">
            <div className="grid grid-cols-2 gap-4 pb-4 border-b border-gray-100">
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Auditor Name</span>
                <span className="font-semibold text-gray-900">{selectedAuditor.name}</span>
              </div>
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Organization</span>
                <span className="font-semibold text-gray-900">{selectedAuditor.designation || "External Authority"}</span>
              </div>
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Email</span>
                <span>{selectedAuditor.email || "N/A"}</span>
              </div>
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Phone</span>
                <span>{selectedAuditor.phone || "N/A"}</span>
              </div>
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Status</span>
                <Badge variant={selectedAuditor.status === "ACTIVE" ? "emerald" : "rose"}>
                  {selectedAuditor.status}
                </Badge>
              </div>
              <div>
                <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Key Version</span>
                <Badge variant="blue">Version {selectedAuditor.key_version}</Badge>
              </div>
            </div>

            <div>
              <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block mb-1">Registered PEKS Public Key</span>
              <pre className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-2xs font-mono select-all overflow-x-auto max-h-48 custom-scrollbar">
                {selectedAuditor.public_key}
              </pre>
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-2 text-2xs text-gray-500 font-light">
              <div>
                <span>Created: {new Date(selectedAuditor.created_at).toLocaleString()}</span>
              </div>
              <div className="text-right">
                <span>Updated: {new Date(selectedAuditor.updated_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* ROTATED KEY MODAL */}
      <Modal
        isOpen={!!rotatedKey}
        onClose={() => setRotatedKey(null)}
        title="🔑 Rotated Keypair Credentials"
        footer={
          <div className="flex gap-2 justify-end w-full">
            <Button variant="secondary" onClick={handleCopyRotatedKey}>
              {copiedKey ? "Copied ✔" : "Copy New Private Key"}
            </Button>
            <Button variant="primary" onClick={() => setRotatedKey(null)} className="border-none bg-blue-600 hover:bg-blue-500">
              Done
            </Button>
          </div>
        }
        className="max-w-lg"
      >
        <p className="text-xs text-rose-600 mb-4 font-sans font-semibold">
          This rotated private key is shown ONLY once. Make sure to download or copy it immediately!
        </p>
        <div className="space-y-2">
          <span className="text-3xs font-bold text-gray-400 uppercase font-mono tracking-wider block">Auditor Name: {rotatedAuditorName}</span>
          <textarea
            readOnly
            value={rotatedKey || ""}
            className="w-full h-44 border border-gray-250 bg-gray-50 p-3 rounded-xl font-mono text-2xs text-gray-800 select-all custom-scrollbar focus:outline-none"
          />
        </div>
      </Modal>

      {/* TIMELINE SIDE DRAWER */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden font-sans">
          <div className="absolute inset-0 bg-black/45 backdrop-blur-xs transition-opacity" onClick={() => setIsDrawerOpen(false)} />
          <div className="absolute inset-y-0 right-0 max-w-full flex">
            <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col">
              
              {/* Drawer Header */}
              <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                <div>
                  <h3 className="text-base font-bold text-gray-900">Auditor Search Timeline</h3>
                  <p className="text-xs text-gray-500 font-light mt-0.5">{selectedAuditor?.name}</p>
                </div>
                <button onClick={() => setIsDrawerOpen(false)} className="text-gray-400 hover:text-gray-600 focus:outline-none cursor-pointer">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-4">
                {loadingLogs ? (
                  <div className="py-12 flex justify-center items-center">
                    <Spinner text="Loading activities..." />
                  </div>
                ) : logs.length === 0 ? (
                  <div className="py-12 text-center text-gray-500 text-xs font-light">
                    No activity logs recorded for this auditor in the timeline directory.
                  </div>
                ) : (
                  <div className="relative border-l border-gray-150 pl-4 space-y-6">
                    {logs.map((log) => (
                      <div key={log.id} className="relative">
                        {/* Timeline node icon */}
                        <div className={`absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 border-white ${log.success ? "bg-emerald-500" : "bg-rose-500"}`} />
                        
                        <div className="bg-gray-50 rounded-xl p-3.5 border border-gray-100 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-3xs text-gray-400 font-mono">
                              {new Date(log.created_at).toLocaleString()}
                            </span>
                            <Badge variant={log.success ? "emerald" : "rose"} className="text-3xs px-1.5 py-0">
                              {log.success ? "Success" : "Failed"}
                            </Badge>
                          </div>

                          <div className="space-y-1 text-xs">
                            <div>
                              <span className="text-3xs font-semibold text-gray-400 uppercase font-mono tracking-wider">Keyword Hash</span>
                              <p className="font-mono text-2xs text-gray-700 select-all overflow-hidden text-ellipsis">{log.keyword_hash}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-2 pt-1 border-t border-gray-100 text-2xs text-gray-500 font-light">
                              <div>
                                <span>Matches: <strong className="text-gray-700 font-semibold">{log.total_matches}</strong></span>
                              </div>
                              <div className="text-right">
                                <span>Time: <strong className="text-gray-700 font-semibold">{log.execution_time_ms}ms</strong></span>
                              </div>
                            </div>

                            {log.key_version && (
                              <div className="text-2xs text-gray-400 font-mono">
                                Key Version: v{log.key_version}
                              </div>
                            )}

                            {!log.success && log.failure_reason && (
                              <div className="mt-1 text-rose-700 font-medium text-2xs bg-rose-50 p-1.5 rounded-md">
                                Reason: {log.failure_reason}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Drawer Footer */}
              <div className="p-4 bg-gray-50 border-t border-gray-100 flex justify-end">
                <Button variant="secondary" onClick={() => setIsDrawerOpen(false)} className="text-xs">
                  Close Timeline
                </Button>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
