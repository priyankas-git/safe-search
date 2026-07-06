# Project File Structure

This document provides a comprehensive overview of the `safe-search` project file structure, including a directory tree and a detailed summary of every file in the codebase.

---

## Directory Tree

```text
safe-search/
├── 🔑 Auditor Private Keys (Sample credentials)
│   ├── [HDFC](file:///home/spidy/Desktop/projects/safe-search/HDFC)
│   ├── [ICICI](file:///home/spidy/Desktop/projects/safe-search/ICICI)
│   ├── [IDFC](file:///home/spidy/Desktop/projects/safe-search/IDFC)
│   └── [LIC](file:///home/spidy/Desktop/projects/safe-search/LIC)
├── ⚙️ Root Configuration & Documentation
│   ├── [README.md](file:///home/spidy/Desktop/projects/safe-search/README.md)
│   ├── [render.yaml](file:///home/spidy/Desktop/projects/safe-search/render.yaml)
│   ├── [summary.md](file:///home/spidy/Desktop/projects/safe-search/summary.md)
│   └── [url endpoints](file:///home/spidy/Desktop/projects/safe-search/url%20endpoints)
├── 🔌 Backend Application (Django REST API)
│   ├── [backend/.dockerignore](file:///home/spidy/Desktop/projects/safe-search/backend/.dockerignore)
│   ├── [backend/.env](file:///home/spidy/Desktop/projects/safe-search/backend/.env)
│   ├── [backend/Dockerfile](file:///home/spidy/Desktop/projects/safe-search/backend/Dockerfile)
│   ├── [backend/requirements.txt](file:///home/spidy/Desktop/projects/safe-search/backend/requirements.txt)
│   └── securematch/ (Django Project Root)
│       ├── [manage.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/manage.py)
│       ├── securematch/ (Core Project App)
│       │   ├── [__init__.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/__init__.py)
│       │   ├── [asgi.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/asgi.py)
│       │   ├── [settings.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/settings.py)
│       │   ├── [urls.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/urls.py)
│       │   └── [wsgi.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/wsgi.py)
│       ├── crypto_engine/ (Cryptographic Logic Layer)
│       │   ├── [__init__.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/__init__.py)
│       │   ├── [admin.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/admin.py)
│       │   ├── [apps.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/apps.py)
│       │   ├── [key_manager.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/key_manager.py)
│       │   ├── [models.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/models.py)
│       │   ├── [peks.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py)
│       │   ├── [sse.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py)
│       │   ├── [tests.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/tests.py)
│       │   └── [views.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/views.py)
│       └── documents/ (Documents Index & Search App)
│           ├── [__init__.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/__init__.py)
│           ├── [admin.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/admin.py)
│           ├── [apps.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/apps.py)
│           ├── [constants.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/constants.py)
│           ├── [models.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/models.py)
│           ├── [tests.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/tests.py)
│           ├── [urls.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/urls.py)
│           ├── [utils.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/utils.py)
│           ├── [views.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/views.py)
│           └── migrations/
│               └── ...
└── 💻 Frontend Application (React + Vite + Tailwind CSS v4)
    ├── [frontend/README.md](file:///home/spidy/Desktop/projects/safe-search/frontend/README.md)
    ├── [frontend/eslint.config.js](file:///home/spidy/Desktop/projects/safe-search/frontend/eslint.config.js)
    ├── [frontend/index.html](file:///home/spidy/Desktop/projects/safe-search/frontend/index.html)
    ├── [frontend/package.json](file:///home/spidy/Desktop/projects/safe-search/frontend/package.json)
    ├── [frontend/vite.config.js](file:///home/spidy/Desktop/projects/safe-search/frontend/vite.config.js)
    └── src/
        ├── [App.css](file:///home/spidy/Desktop/projects/safe-search/frontend/src/App.css)
        ├── [App.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/App.jsx)
        ├── [index.css](file:///home/spidy/Desktop/projects/safe-search/frontend/src/index.css)
        ├── [main.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/main.jsx)
        ├── components/ (UI View Pages & Elements)
        │   ├── [CreateAuditorCard.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/CreateAuditorCard.jsx)
        │   ├── [MetricsPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/MetricsPage.jsx)
        │   ├── [Navbar.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/Navbar.jsx)
        │   ├── [SearchPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/SearchPage.jsx)
        │   ├── [StoragePage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/StoragePage.jsx)
        │   └── [UploadPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/UploadPage.jsx)
        ├── pages/ (React Page Shells)
        │   └── [Dashboard.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/pages/Dashboard.jsx)
        ├── services/ (Axios REST Connectors)
        │   ├── [api.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/api.js)
        │   ├── [auditorService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/auditorService.js)
        │   ├── [externalSearchService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/externalSearchService.js)
        │   ├── [internalSearchService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/internalSearchService.js)
        │   └── [uploadService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/uploadService.js)
        └── utils/ (Browser Helpers)
            ├── [crypto.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/utils/crypto.js)
            └── [errorHandler.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/utils/errorHandler.js)
```

---

## Detailed File Summaries

### Root Level Files

| File | Purpose |
| :--- | :--- |
| **[HDFC](file:///home/spidy/Desktop/projects/safe-search/HDFC)** | Sample PEM RSA private key file for the HDFC external auditor identity, used in testing auditor searches. |
| **[ICICI](file:///home/spidy/Desktop/projects/safe-search/ICICI)** | Sample PEM RSA private key file for the ICICI external auditor identity. |
| **[IDFC](file:///home/spidy/Desktop/projects/safe-search/IDFC)** | Sample PEM RSA private key file for the IDFC external auditor identity. |
| **[LIC](file:///home/spidy/Desktop/projects/safe-search/LIC)** | Sample PEM RSA private key file for the LIC external auditor identity. |
| **[README.md](file:///home/spidy/Desktop/projects/safe-search/README.md)** | High-level instructions covering implementation logic, database schema, REST endpoints overview, environment setup, and local run guides. |
| **[render.yaml](file:///home/spidy/Desktop/projects/safe-search/render.yaml)** | Environment infrastructure configurations for deploying the containerized Django service to the Render cloud platform. |
| **[url endpoints](file:///home/spidy/Desktop/projects/safe-search/url%20endpoints)** | Plain text documentation detailing available REST API endpoints and HTTP methods for reference. |
| **[summary.md](file:///home/spidy/Desktop/projects/safe-search/summary.md)** | Comprehensive project design documentation outlining architecture rationale, backend frameworks, cryptographic algorithms, models, and UI flows. |

---

### Backend Application (`backend/`)

#### Build & Environment Configurations
- **[backend/.dockerignore](file:///home/spidy/Desktop/projects/safe-search/backend/.dockerignore)**: Defines paths, virtual environments, and caches excluded from being copied into the backend Docker image.
- **[backend/.env](file:///home/spidy/Desktop/projects/safe-search/backend/.env)**: Holds local development secrets, such as API configurations, debug controls, database connection strings, and the cryptographic master key base64 seed.
- **[backend/Dockerfile](file:///home/spidy/Desktop/projects/safe-search/backend/Dockerfile)**: Script instructions to build the Django Docker container based on Python 3.11-slim, compiling packages and hosting via Gunicorn on port `8000`.
- **[backend/requirements.txt](file:///home/spidy/Desktop/projects/safe-search/backend/requirements.txt)**: Python package list detailing dependencies like `Django`, `djangorestframework`, `cryptography`, `psycopg2-binary`, `gunicorn`, and `whitenoise`.

#### Django Configuration Settings
- **[backend/securematch/manage.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/manage.py)**: Central Django administrative CLI helper utility.
- **[backend/securematch/securematch/settings.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/settings.py)**: Global config file for Django, defining database setup (PostgreSQL), CORS headers, rate-limiting throttle scopes (`upload`, `search`), WhiteNoise middleware, and security variables.
- **[backend/securematch/securematch/urls.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/urls.py)**: Main URL routing table directing admin and `/api/` traffic to respective sub-modules.
- **[backend/securematch/securematch/asgi.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/asgi.py)** / **[wsgi.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/securematch/wsgi.py)**: Application entry points mapping the Django project to modern ASGI/WSGI web service gateways.

#### Cryptographic Engine (`backend/securematch/crypto_engine/`)
- **[key_manager.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/key_manager.py)**: Functions [load_master_key](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/key_manager.py#L9) and [derive_keys](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/key_manager.py#L23) that decode the environmental `MASTER_KEY` and apply HKDF-SHA256 key derivation to obtain subkeys for symmetric document encryption (AES) and index verification (HMAC).
- **[peks.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py)**: Houses RSA asymmetric signature utilities: [generate_keypair](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py#L12) to produce 2048-bit keypairs, [hash_keyword](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py#L44) to hash keywords deterministically using SHA-256, [generate_trapdoor_private](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py#L57) for signing keyword hashes, and [verify_signature](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/peks.py#L88) to validate signed requests from auditors.
- **[sse.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py)**: Implements Symmetric Searchable Encryption functions. Contains [encrypt_document](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py#L21) / [decrypt_document](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py#L41) using AES-256-GCM alongside [generate_token](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py#L64) / [generate_trapdoor](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/crypto_engine/sse.py#L82) using HMAC-SHA256 to hash keywords on searchable fields.

#### Documents Database Management & Business Logic (`backend/securematch/documents/`)
- **[constants.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/constants.py)**: Lists [SEARCHABLE_FIELDS](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/constants.py#L1) (`pan`, `compliance_flag`, `name`, `customer_id`, `aadhaar`) subjected to indexing.
- **[models.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/models.py)**: Django ORM database model mappings:
  - `EncryptedDocument`: Stores JSON values containing encrypted data blobs (`nonce` + `ciphertext`).
  - `SearchTokenIndex`: Inverted token lookup index storing internal tokens (HMAC-SHA256) and external tokens (SHA-256 deterministic hashes) pointing back to `EncryptedDocument` relations.
  - `Auditor`: Table listing registered external auditors, their key versions, and public keys.
  - `ExternalSearchAudit`: Audit logging registry tracking request metadata (success state, key version, timing records).
- **[urls.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/urls.py)**: Maps URL path extensions to corresponding API classes (e.g., `upload/`, `search/internal/`, `search/external/`, metrics).
- **[utils.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/utils.py)**: Standardizes API response structures via helper functions [success_response](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/utils.py#L4) and [error_response](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/utils.py#L26).
- **[views.py](file:///home/spidy/Desktop/projects/safe-search/backend/securematch/documents/views.py)**: Controllers coordinating API logic:
  - `UploadDocumentView`: Throttled POST handler to encrypt raw data and save search indices.
  - `InternalSearchView`: Search endpoint for internal analysts using HMAC trapdoors (returns fully decrypted documents).
  - `ExternalSearchView`: Auditor query endpoint verifying signatures and returning fixed-size padded encrypted payloads (mitigates size-based metadata leaks).
  - `CreateAuditorView` / `DeleteAuditorView` / `RotateAuditorKeyView`: REST interfaces managing the auditor directory and RSA key updates.
  - `InternalMetricsView` / `ExternalMetricsView`: Exposes real-time system performance data, transaction counters, and auditor metrics.

---

### Frontend Application (`frontend/`)

#### React App Shell Configuration
- **[frontend/README.md](file:///home/spidy/Desktop/projects/safe-search/frontend/README.md)**: Standard manual listing steps to bootstrap and compile the React application.
- **[frontend/eslint.config.js](file:///home/spidy/Desktop/projects/safe-search/frontend/eslint.config.js)**: Configures rules for checking script syntax and style guidelines.
- **[frontend/index.html](file:///home/spidy/Desktop/projects/safe-search/frontend/index.html)**: Main HTML container rendering the React elements.
- **[frontend/package.json](file:///home/spidy/Desktop/projects/safe-search/frontend/package.json)**: Declares NPM dependencies (Vite, React 19, Axios, Tailwind CSS v4) and scripts (`dev`, `build`, `preview`).
- **[frontend/vite.config.js](file:///home/spidy/Desktop/projects/safe-search/frontend/vite.config.js)**: Build configs wrapping Vite plugins for bundling React components and loading TailwindCSS.

#### React Scripts & Views (`frontend/src/`)
- **[frontend/src/index.css](file:///home/spidy/Desktop/projects/safe-search/frontend/src/index.css)**: Primary styling sheet loading Tailwind CSS v4 variables and components.
- **[frontend/src/main.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/main.jsx)**: Global React entrypoint bootstrapping the virtual DOM.
- **[frontend/src/App.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/App.jsx)**: Main App layout routing users based on selected roles (analyst vs auditor) and verifying access credentials.
- **[frontend/src/pages/Dashboard.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/pages/Dashboard.jsx)**: Coordinates view presentation by wrapping the main header and mounting tab components depending on user selection.
- **[frontend/src/components/CreateAuditorCard.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/CreateAuditorCard.jsx)**: Multi-step card enabling creation of new auditors and modal overlay for copying the private key.
- **[frontend/src/components/MetricsPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/MetricsPage.jsx)**: Formats stats metrics, logs, and manages key rotations and deletions.
- **[frontend/src/components/Navbar.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/Navbar.jsx)**: Standard navigation header for role identification and switching active tabs.
- **[frontend/src/components/SearchPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/SearchPage.jsx)**: Implements search logic, showing step-by-step logs, generating query-bound HMAC trapdoors (for analysts) or performing client-side signing (for auditors) using the Web Cryptography API.
- **[frontend/src/components/StoragePage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/StoragePage.jsx)**: Unmounted view component containing a simulated visualization of AES-256-GCM ciphertexts and HMAC inverted index values.
- **[frontend/src/components/UploadPage.jsx](file:///home/spidy/Desktop/projects/safe-search/frontend/src/components/UploadPage.jsx)**: Provides input fields (Form or raw JSON) allowing analysts to upload new records.

#### Connectors & Browser Utilities (`frontend/src/services/` & `frontend/src/utils/`)
- **[frontend/src/services/api.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/api.js)**: Creates Axios HTTP wrapper pointing requests to the Render web service base URL.
- **[frontend/src/services/auditorService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/auditorService.js)**: Functions to rotate auditor keys and retrieve search audit logs.
- **[frontend/src/services/externalSearchService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/externalSearchService.js)**: Executes client-side hashing and signs values before posting requests to the external auditor search API.
- **[frontend/src/services/internalSearchService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/internalSearchService.js)**: Sends analyst search requests to the internal SSE search service.
- **[frontend/src/services/uploadService.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/services/uploadService.js)**: Handles uploading new documents to the storage endpoint.
- **[frontend/src/utils/crypto.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/utils/crypto.js)**: Web Cryptography API integration for browser operations: normalizes inputs, generates SHA-256 hash strings, parses private key PEMs, and signs queries using RSA-PSS.
- **[frontend/src/utils/errorHandler.js](file:///home/spidy/Desktop/projects/safe-search/frontend/src/utils/errorHandler.js)**: Parses API exception structures to return standardized error codes and friendly descriptions.
