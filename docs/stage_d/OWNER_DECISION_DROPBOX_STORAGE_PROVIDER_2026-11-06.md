# Owner Decision Addendum — Dropbox as Box Substitute
## 2026-11-06 — append-only

**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Decision basis:** Owner instruction in the active project conversation: “اذا كان يمكن استخدام Dropbox بدلا من Box فقم بذلك واعتمده”.  
**Scope:** Select Dropbox as the project's approved connected external-storage provider in place of Box for the Motorcycle Simulation preservation/rescue workflow.

### Decision
1. Dropbox is adopted as the designated external archive destination instead of Box. The project workflow should use the connected Dropbox integration and the existing rescue namespace:
   `/Motorcycle-Simulation-Rescue-2026-11-05/`.
2. The existing `secondary_verified_mirror/` folder may be used for a second Dropbox copy where preservation of a separate path is useful, but it is **not** an independent provider or failure domain.
3. Do not require Box for future project preservation steps while Dropbox remains connected, writable, and within quota/permissions.
4. This provider selection does not amend v2.4.0, REV6, business rules, trial identities, artifact history, or any phase acceptance criteria.
5. No historical Artifact or manifest may be deleted, replaced, or silently rewritten. Continue append-only evidence recording.

### Live verification at decision intake
- GitHub repository: `yasmin977209-ux/motorcycle-simulation`.
- Working branch HEAD observed before this addendum: `13115de20d1bf0c9235fb09441a5167dd1c745bc`.
- `main` HEAD observed: `01a6f79eedc522bb734ed9c5ea31beee581f2468` (read-only).
- Dropbox rescue folder exists and is readable at `/Motorcycle-Simulation-Rescue-2026-11-05/`.
- Root listing returned nine archive files, total listed file size `1,375,253,616` bytes.
- `secondary_verified_mirror/` exists and contains three mirrored large archives (Artifacts `13288779998`, `13369179742`, `12998778418`).
- Dropbox folder metadata/listing confirms availability and readable metadata. This intake did not independently retrieve all archive bytes or run ZIP restore tests.

### Preservation status — not promoted
Dropbox is approved and adopted as the Box substitute, but this decision alone does **not** close Global Preservation Gate. The following remain required:
- byte-level SHA-256 comparison against the exact GitHub Artifact bytes/digests;
- ZIP CRC/member inventory and internal manifest/hash verification;
- successful restore test from Dropbox;
- a second durable copy in a genuinely independent provider/failure domain, or other method explicitly satisfying REV6;
- preservation and transfer of all remaining mandatory Artifacts, including the E2 replay set, without confusing Replay Reconstruction with original historical evidence.

Until those checks are completed:
`Global Preservation Gate = BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`.

### Operational effect
Use Dropbox for new authorized external-preservation copies and readbacks. Keep GitHub `main` read-only; make any repository documentation changes only on the working branch. This is a storage-provider selection, not a declaration of phase closure or final acceptance.
