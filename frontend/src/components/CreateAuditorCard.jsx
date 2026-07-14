import { useState } from "react";
import {
  ContentCard,
  InputGroup,
  FieldLabel,
  TextInput,
  Button,
  Modal,
} from "./ui";

export default function CreateAuditorCard({ createAuditor, showToast }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [designation, setDesignation] = useState("");
  const [loading, setLoading] = useState(false);
  const [privateKey, setPrivateKey] = useState(null);
  const [tempPassword, setTempPassword] = useState("");
  const [username, setUsername] = useState("");
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedPassword, setCopiedPassword] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
      showToast("Please enter an auditor identity name", "warning");
      return;
    }

    try {
      setLoading(true);
      const res = await createAuditor({
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        designation: designation.trim() || null,
        status: "ACTIVE"
      });

      const creds = res?.data;
      if (creds) {
        setPrivateKey(creds.private_key);
        setTempPassword(creds.temporary_password || "");
        setUsername(creds.username || "");
        setName("");
        setEmail("");
        setPhone("");
        setDesignation("");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyKey = async () => {
    if (privateKey) {
      await navigator.clipboard.writeText(privateKey);
      setCopiedKey(true);
      showToast("Private key copied to clipboard", "success");
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleCopyPassword = async () => {
    if (tempPassword) {
      await navigator.clipboard.writeText(tempPassword);
      setCopiedPassword(true);
      showToast("Temporary password copied to clipboard", "success");
      setTimeout(() => setCopiedPassword(false), 2000);
    }
  };

  const handleClose = () => {
    setPrivateKey(null);
    setTempPassword("");
    setUsername("");
  };

  const modalFooter = (
    <div className="flex gap-2 justify-end w-full">
      <Button variant="secondary" onClick={handleCopyKey}>
        {copiedKey ? "Key Copied ✔" : "Copy Private Key"}
      </Button>
      {tempPassword && (
        <Button variant="secondary" onClick={handleCopyPassword}>
          {copiedPassword ? "Password Copied ✔" : "Copy Temp Password"}
        </Button>
      )}
      <Button
        variant="primary"
        onClick={handleClose}
        className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold border-none"
      >
        I Have Stored Credentials Securely
      </Button>
    </div>
  );

  return (
    <>
      <ContentCard>
        <h3 className="font-bold mb-2 text-base sm:text-lg text-gray-900 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
          Register New Auditor
        </h3>
        <p className="text-gray-500 text-xs mb-5 font-light">
          Provision an auditor profile, assign the role, and generate their cryptographic credential packet.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <InputGroup>
            <FieldLabel>Name / Identity *</FieldLabel>
            <TextInput
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Authority name (e.g. RBI Auditor)"
            />
          </InputGroup>
          
          <InputGroup>
            <FieldLabel>Organization / Designation</FieldLabel>
            <TextInput
              value={designation}
              onChange={(e) => setDesignation(e.target.value)}
              placeholder="Organization name (e.g. Reserve Bank of India)"
            />
          </InputGroup>

          <InputGroup>
            <FieldLabel>Email Address</FieldLabel>
            <TextInput
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="auditor@org.com"
            />
          </InputGroup>

          <InputGroup>
            <FieldLabel>Phone Number</FieldLabel>
            <TextInput
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+919999999999"
            />
          </InputGroup>
        </div>

        <div className="flex justify-end mt-4">
          <Button
            onClick={handleCreate}
            loading={loading}
            className="w-full sm:w-auto px-6 py-2.5 font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition"
          >
            {loading ? "Registering..." : "Add Auditor Profile"}
          </Button>
        </div>
      </ContentCard>

      <Modal
        isOpen={!!privateKey}
        onClose={handleClose}
        title="⚠️ Secure Credentials Provisioned"
        footer={modalFooter}
        className="max-w-xl"
      >
        <p className="text-xs text-rose-600 mb-4 font-sans font-semibold">
          These credentials are shown ONLY once. Please copy and store them securely.
          The private key is required for signing search queries.
        </p>

        <div className="space-y-4 mb-4 font-sans text-sm">
          {username && (
            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
              <span className="text-xs text-gray-500 block font-light">Portal Username</span>
              <span className="font-mono font-semibold text-gray-900">{username}</span>
            </div>
          )}
          {tempPassword && (
            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
              <span className="text-xs text-gray-500 block font-light">Temporary Portal Password</span>
              <span className="font-mono font-semibold text-emerald-600 select-all">{tempPassword}</span>
            </div>
          )}
          <div>
            <span className="text-xs text-gray-500 block font-light mb-1">Generated Private Key (PEM format)</span>
            <textarea
              readOnly
              value={privateKey || ""}
              className="w-full h-40 border border-gray-250 bg-gray-50 p-3 rounded-xl font-mono text-2xs text-gray-800 select-all custom-scrollbar focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </>
  );
}