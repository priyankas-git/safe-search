import { useState, useEffect } from "react";
import api from "./services/api";
import Dashboard from "./pages/Dashboard";
import Toast from "./components/Toast";
import { Spinner } from "./components/Loader";
import { sha256Hex, signHashHex, verifySignatureHex } from "./utils/crypto";
import { handleApiError } from "./utils/errorHandler";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";
import PermissionRoute from "./routes/PermissionRoute";
import { Roles } from "./constants/roles";
import { hasRole, hasAnyRole, getRoleFromUser } from "./config/permissions";

// UI Components
import {
  Button,
  TextInput,
  PasswordInput,
  FieldLabel,
  InputGroup,
  ContentCard,
  StatusBadge,
} from "./components/ui";

// Admin Dashboard Components & Pages
import AdminLayout from "./layouts/AdminLayout";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminIAM from "./pages/admin/IAM";
import AdminAuditors from "./pages/admin/Auditors";
import AdminMetrics from "./pages/admin/Metrics";
import AdminProfile from "./pages/admin/Profile";
import AdminDocuments from "./pages/admin/Documents";
import AdminSearch from "./pages/admin/Search";
import AdminSettings from "./pages/admin/Settings";

export default function App() {
  const { login: authLogin, logout: authLogout, isLoading } = useAuth();

  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  const navigate = (path) => {
    window.history.pushState(null, "", path);
    setCurrentPath(path);
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  const [role, setRole] = useState(() => {
    const saved = localStorage.getItem("roleState");
    if (!saved) return null;

    try {
      return JSON.parse(saved);
    } catch (error) {
      console.warn("Ignoring invalid roleState in localStorage", error);
      localStorage.removeItem("roleState");
      return null;
    }
  });

  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  const [externalAuditors, setExternalAuditors] = useState([]);
  const [selectedAuditor, setSelectedAuditor] = useState(null);
  const [privateKeyInput, setPrivateKeyInput] = useState("");
  const [loadingAuditors, setLoadingAuditors] = useState(false);
  const [toast, setToast] = useState(null);

  const updateRoleState = (newRole) => {
    setRole(newRole);
    if (newRole) {
      localStorage.setItem("roleState", JSON.stringify(newRole));
    } else {
      localStorage.removeItem("roleState");
    }
  };

  const showToast = (message, type = "info") => {
    setToast({ message, type });
  };

  const logout = async () => {
    await authLogout();
    updateRoleState(null);
    setSelectedAuditor(null);
    setPrivateKeyInput("");
    showToast("Logged out successfully", "info");
    navigate("/");
  };

  const fetchAuditors = async () => {
    try {
      setLoadingAuditors(true);
      const res = await api.get("/api/metrics/internal/");
      const data = res.data?.data || {};
      const auditors = data.auditors || [];
      setExternalAuditors(auditors);
      return auditors;
    } catch (err) {
      console.error("Failed to fetch auditors", err);
      showToast("Failed to retrieve auditors directory", "error");
      return [];
    } finally {
      setLoadingAuditors(false);
    }
  };

  const handleAdminLogin = async () => {
    if (!usernameInput.trim() || !passwordInput.trim()) {
      showToast("Username and password required", "warning");
      return;
    }

    try {
      setLoggingIn(true);
      const res = await authLogin(usernameInput, passwordInput);
      if (res.success) {
        if (!hasRole(res.user, Roles.ADMINISTRATOR)) {
          showToast("Access denied: You do not have Super Administrator privileges", "error");
          await authLogout();
          return;
        }

        updateRoleState({ type: "admin" });
        showToast("Logged in as Super Administrator", "success");
        setUsernameInput("");
        setPasswordInput("");
        navigate("/admin");
      }
    } catch (err) {
      console.error(err);
      const { message } = handleApiError(err);
      showToast(message || "Invalid username or password", "error");
    } finally {
      setLoggingIn(false);
    }
  };

  const handleInternalLogin = async () => {
    if (!usernameInput.trim() || !passwordInput.trim()) {
      showToast("Username and password required", "warning");
      return;
    }

    try {
      setLoggingIn(true);
      const res = await authLogin(usernameInput, passwordInput);
      if (res.success) {
        const allowedRoles = [Roles.INTERNAL_ANALYST, Roles.COMPLIANCE_OFFICER, Roles.READ_ONLY_ANALYST];
        if (!hasAnyRole(res.user, allowedRoles)) {
          showToast("Access denied: This portal is for internal operational teams only", "error");
          await authLogout();
          return;
        }

        updateRoleState({ type: "internal" });
        showToast(`Logged in to Internal Portal as ${getRoleFromUser(res.user)}`, "success");
        setUsernameInput("");
        setPasswordInput("");
      }
    } catch (err) {
      console.error(err);
      const { message } = handleApiError(err);
      showToast(message || "Invalid username or password", "error");
    } finally {
      setLoggingIn(false);
    }
  };

  const handleExternalLogin = async () => {
    if (!usernameInput.trim() || !passwordInput.trim()) {
      showToast("Username and password required", "warning");
      return;
    }

    try {
      setLoggingIn(true);
      const res = await authLogin(usernameInput, passwordInput);
      if (res.success) {
        if (!hasRole(res.user, Roles.EXTERNAL_AUDITOR)) {
          showToast("Access denied: Please use the External Auditor portal", "error");
          await authLogout();
          return;
        }

        updateRoleState({ type: "external_select" });
        showToast("Authentication successful", "success");
        setUsernameInput("");
        setPasswordInput("");
        await fetchAuditors();
      }
    } catch (err) {
      console.error(err);
      const { message } = handleApiError(err);
      showToast(message || "Invalid username or password", "error");
    } finally {
      setLoggingIn(false);
    }
  };

  const handleExternalContinue = async () => {
    if (!privateKeyInput.trim()) {
      showToast("Auditor private key required", "warning");
      return;
    }

    if (!selectedAuditor) {
      showToast("Select an auditor identity", "warning");
      return;
    }

    try {
      const probe = `auditor-probe:${selectedAuditor.auditor_id}`;
      const probeHash = await sha256Hex(probe);
      const signature = await signHashHex(probeHash, privateKeyInput);
      let verifiedAuditor = selectedAuditor;

      try {
        const res = await api.post("/api/auditor/verify/", {
          auditor_id: selectedAuditor.auditor_id,
          signature,
        });
        verifiedAuditor = res.data?.data || selectedAuditor;
      } catch (err) {
        const status = err.response?.status;

        if (status !== 404) {
          throw err;
        }

        const auditors = await fetchAuditors();
        const freshAuditor = auditors.find(
          (auditor) => auditor.auditor_id === selectedAuditor.auditor_id
        );

        if (!freshAuditor) {
          showToast("Selected auditor no longer exists", "error");
          return;
        }

        if (!freshAuditor.public_key) {
          showToast(
            "Backend does not support /api/auditor/verify/ and auditor public key is unavailable",
            "error"
          );
          return;
        }

        const isValid = await verifySignatureHex(
          probeHash,
          signature,
          freshAuditor.public_key
        );

        if (!isValid) {
          showToast("Private key does not match selected auditor", "error");
          return;
        }

        verifiedAuditor = freshAuditor;
      }

      setSelectedAuditor(verifiedAuditor);

      updateRoleState({
        type: "external",
        auditor: verifiedAuditor,
        privateKey: privateKeyInput,
      });

      showToast(`Logged in as ${verifiedAuditor.name}`, "success");
    } catch (err) {
      console.error(err);
      const { message } = handleApiError(err);
      showToast(message || "Invalid private key format or mismatched credentials", "error");
    }
  };

  // Sync Axios auto-logout with App role state
  useEffect(() => {
    const handleAuthLogout = () => {
      updateRoleState(null);
      setSelectedAuditor(null);
      setPrivateKeyInput("");
    };
    window.addEventListener("auth-logout", handleAuthLogout);
    return () => {
      window.removeEventListener("auth-logout", handleAuthLogout);
    };
  }, []);

  const { user: authUser, isAuthenticated: isUserAuthenticated } = useAuth();

  useEffect(() => {
    if (isUserAuthenticated && authUser) {
      const isPathAdmin = currentPath.startsWith("/admin");
      const isAdmin = hasRole(authUser, Roles.ADMINISTRATOR);

      console.log(`[TEMP][App.jsx] Path checking: isPathAdmin=${isPathAdmin}, isAdmin=${isAdmin}, userRole=${getRoleFromUser(authUser)}`);

      if (isPathAdmin && !isAdmin) {
        showToast("Access denied: You do not have Super Administrator privileges", "error");
        logout();
      } else if (!isPathAdmin && isAdmin) {
        navigate("/admin");
      }
    }
  }, [isUserAuthenticated, authUser, currentPath]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Spinner text="Loading..." />
      </div>
    );
  }

  // ===============================
  // AUTH SCREENS ROUTING
  // ===============================
  const renderAuthScreens = () => {
    const isAdminPath = currentPath.startsWith("/admin");
    const showAdminLogin = isAdminPath || (role && role.type === "admin_login");

    // 2. Admin Login Form (checks both route and role state)
    if (showAdminLogin) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6 py-12">
          <ContentCard className="w-full max-w-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Super Administrator Login</h2>
            <p className="text-xs text-gray-500 mb-6 font-medium">Provide your username and password credentials to access the administrative portal.</p>
            <div className="space-y-4">
              <InputGroup>
                <FieldLabel>Username</FieldLabel>
                <TextInput
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder="Enter admin username"
                />
              </InputGroup>
              <InputGroup>
                <FieldLabel>Password</FieldLabel>
                <PasswordInput
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="Enter admin password"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleAdminLogin();
                  }}
                />
              </InputGroup>
              <Button
                variant="primary"
                onClick={handleAdminLogin}
                loading={loggingIn}
                className="w-full py-3"
              >
                {loggingIn ? "Logging in..." : "Login"}
              </Button>
            </div>
            <Button
              variant="ghost"
              onClick={() => {
                setUsernameInput("");
                setPasswordInput("");
                if (currentPath.startsWith("/admin")) {
                  navigate("/");
                }
                updateRoleState(null);
              }}
              className="mt-6 w-full text-center text-xs text-gray-500 hover:text-gray-800 transition font-medium"
            >
              ← Back
            </Button>
          </ContentCard>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

    // 1. Entry Screen (3-Portal Layout)
    if (!role) {
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 py-12 relative font-sans">
          <div className="text-center mb-10 select-none">
            <div className="w-14 h-14 bg-blue-600 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold mb-2 text-gray-900">Secure Encrypted Search System</h1>
            <p className="text-gray-500 max-w-md mx-auto text-sm">AES-256 Encryption • HMAC Trapdoors • SSE/PEKS Protocol</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-6xl w-full">
            {/* PORTAL 1: SUPER ADMINISTRATOR */}
            <ContentCard className="flex flex-col justify-between group hover:border-blue-500/50 transition">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Super Administrator</h2>
                <p className="text-gray-550 text-sm mb-5">Complete administrative access to SecureMatch.</p>
                <ul className="text-sm space-y-3 mb-6 text-gray-600">
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>User Management</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-655"></span>Auditor Management</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>System Metrics</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>Full Administrative Access</li>
                </ul>
              </div>
              <Button
                variant="primary"
                onClick={() => updateRoleState({ type: "admin_login" })}
                className="w-full py-2.5"
              >
                Continue to Admin Portal
              </Button>
            </ContentCard>

            {/* PORTAL 2: INTERNAL PORTAL */}
            <ContentCard className="flex flex-col justify-between group hover:border-blue-500/50 transition">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Internal Portal</h2>
                <p className="text-gray-550 text-sm mb-5">Secure operational workspace for internal teams.</p>
                <ul className="text-sm space-y-3 mb-6 text-gray-600">
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>Upload encrypted documents</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>Internal encrypted search (SSE)</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>View encrypted storage</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-650"></span>Access internal metrics</li>
                </ul>
              </div>
              <Button
                variant="primary"
                onClick={() => updateRoleState({ type: "internal_login" })}
                className="w-full py-2.5"
              >
                Continue to Internal Portal
              </Button>
            </ContentCard>

            {/* PORTAL 3: EXTERNAL AUDITOR PORTAL */}
            <ContentCard className="flex flex-col justify-between group hover:border-emerald-500/50 transition">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">External Auditor Portal</h2>
                <p className="text-gray-555 text-sm mb-5">Secure search-only workspace for authorized auditors.</p>
                <ul className="text-sm space-y-3 mb-6 text-gray-600">
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>PEKS Search</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>Limited Metrics</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>Secure Auditor Access</li>
                </ul>
              </div>
              <Button
                variant="secondary"
                onClick={() => updateRoleState({ type: "external_login" })}
                className="w-full py-2.5"
              >
                Continue to Auditor Portal
              </Button>
            </ContentCard>
          </div>

          <p className="text-xs text-gray-400 mt-10 text-center max-w-xl font-mono">Role-Based Access Control • SSE • PEKS</p>

          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

    // 3. Internal Login Form
    if (role.type === "internal_login") {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6 py-12">
          <ContentCard className="w-full max-w-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Internal Analyst Login</h2>
            <p className="text-xs text-gray-500 mb-6 font-medium">Provide your username and password credentials to access the operational portal.</p>
            <div className="space-y-4">
              <InputGroup>
                <FieldLabel>Username</FieldLabel>
                <TextInput
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder="Enter username"
                />
              </InputGroup>
              <InputGroup>
                <FieldLabel>Password</FieldLabel>
                <PasswordInput
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="Enter password"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleInternalLogin();
                  }}
                />
              </InputGroup>
              <Button
                variant="primary"
                onClick={handleInternalLogin}
                loading={loggingIn}
                className="w-full py-3"
              >
                {loggingIn ? "Logging in..." : "Login"}
              </Button>
            </div>
            <Button
              variant="ghost"
              onClick={() => {
                setUsernameInput("");
                setPasswordInput("");
                updateRoleState(null);
              }}
              className="mt-6 w-full text-center text-xs text-gray-500 hover:text-gray-800 transition font-medium"
            >
              ← Back
            </Button>
          </ContentCard>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

    // 4. External Login Form
    if (role.type === "external_login") {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6 py-12">
          <ContentCard className="w-full max-w-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">External Auditor Login</h2>
            <p className="text-xs text-gray-500 mb-6 font-medium">Provide your credentials to authenticate and select your auditor identity.</p>
            <div className="space-y-4">
              <InputGroup>
                <FieldLabel>Username</FieldLabel>
                <TextInput
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder="Enter username"
                />
              </InputGroup>
              <InputGroup>
                <FieldLabel>Password</FieldLabel>
                <PasswordInput
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="Enter password"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleExternalLogin();
                  }}
                />
              </InputGroup>
              <Button
                variant="primary"
                onClick={handleExternalLogin}
                loading={loggingIn}
                className="w-full py-3"
              >
                {loggingIn ? "Logging in..." : "Login"}
              </Button>
            </div>
            <Button
              variant="ghost"
              onClick={() => {
                setUsernameInput("");
                setPasswordInput("");
                updateRoleState(null);
              }}
              className="mt-6 w-full text-center text-xs text-gray-500 hover:text-gray-800 transition font-medium"
            >
              ← Back
            </Button>
          </ContentCard>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

    // 5. External Select Screen
    if (role.type === "external_select") {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6 py-12">
          <ContentCard className="w-full max-w-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Auditor Identity</h2>
            <p className="text-xs text-gray-500 mb-6 font-medium">Choose your registered identity and provide the matching private key credentials.</p>

            {loadingAuditors ? (
              <div className="py-8"><Spinner text="Loading auditor registry..." /></div>
            ) : externalAuditors.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-6 border border-dashed rounded-xl mb-6">No auditors available.</p>
            ) : (
              <div className="space-y-2 mb-6">
                {externalAuditors.map((auditor) => (
                  <button
                    key={auditor.auditor_id}
                    onClick={() => setSelectedAuditor(auditor)}
                    className={`w-full border text-left px-4 py-3 rounded-xl transition text-sm flex justify-between items-center cursor-pointer ${
                      selectedAuditor?.auditor_id === auditor.auditor_id
                        ? "bg-gray-100 border-black text-black font-semibold"
                        : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <span>{auditor.name}</span>
                    <span className="text-[10px] bg-gray-150 border px-2 py-0.5 rounded text-gray-500 uppercase font-mono">
                      Ver {auditor.active_key_version}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {selectedAuditor && (
              <div className="space-y-4 animate-[fadeIn_0.2s_ease-out]">
                <InputGroup>
                  <FieldLabel>Auditor Private Key</FieldLabel>
                  <textarea
                    value={privateKeyInput}
                    onChange={(e) => setPrivateKeyInput(e.target.value)}
                    className="w-full border border-gray-250 bg-white rounded-xl p-3 text-xs font-mono h-28 focus:border-blue-500 focus:outline-none text-gray-800 custom-scrollbar"
                    placeholder="-----BEGIN PRIVATE KEY-----&#10;..."
                  />
                </InputGroup>
                <Button
                  variant="primary"
                  onClick={handleExternalContinue}
                  className="w-full py-3"
                >
                  Continue
                </Button>
              </div>
            )}

            <Button
              variant="ghost"
              onClick={() => {
                setSelectedAuditor(null);
                setPrivateKeyInput("");
                authLogout().then(() => updateRoleState(null));
              }}
              className="mt-6 w-full text-center text-xs text-gray-500 hover:text-gray-800 transition font-medium"
            >
              ← Logout
            </Button>
          </ContentCard>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6 py-12">
        <ContentCard className="w-full max-w-md p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Secure Encrypted Search System</h2>
          <p className="text-sm text-gray-500 mb-6">
            The saved session state was invalid, so the app reset to the landing screen.
          </p>
          <Button
            variant="primary"
            onClick={() => updateRoleState(null)}
            className="w-full py-3"
          >
            Return to Start
          </Button>
        </ContentCard>
      </div>
    );
  };

  const isDashboardRole = role && (role.type === "internal" || role.type === "external" || role.type === "admin");
  const isAdminRoute = currentPath.startsWith("/admin");

  let adminPageContent = null;
  if (currentPath === "/admin") {
    adminPageContent = <AdminDashboard navigate={navigate} />;
  } else if (currentPath === "/admin/iam") {
    adminPageContent = <AdminIAM showToast={showToast} />;
  } else if (currentPath === "/admin/auditors") {
    adminPageContent = <AdminAuditors showToast={showToast} />;
  } else if (currentPath === "/admin/documents") {
    adminPageContent = <AdminDocuments showToast={showToast} />;
  } else if (currentPath === "/admin/search") {
    adminPageContent = <AdminSearch showToast={showToast} />;
  } else if (currentPath === "/admin/metrics") {
    adminPageContent = <AdminMetrics />;
  } else if (currentPath === "/admin/settings") {
    adminPageContent = <AdminSettings />;
  } else if (currentPath === "/admin/profile") {
    adminPageContent = <AdminProfile />;
  } else {
    adminPageContent = <AdminDashboard navigate={navigate} />;
  }

  return (
    <ProtectedRoute fallback={renderAuthScreens()}>
      {isAdminRoute ? (
        <RoleRoute allowedRoles={[Roles.ADMINISTRATOR]} fallback={renderAuthScreens()}>
          <AdminLayout
            currentPath={currentPath}
            navigate={navigate}
            user={authUser}
            logout={logout}
          >
            {adminPageContent}
          </AdminLayout>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </RoleRoute>
      ) : isDashboardRole ? (
        <>
          <Dashboard
            role={role.type}
            auditor={role.auditor}
            privateKey={role.privateKey}
            logout={logout}
            showToast={showToast}
          />
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </>
      ) : (
        renderAuthScreens()
      )}
    </ProtectedRoute>
  );
}
