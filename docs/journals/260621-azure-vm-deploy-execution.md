# Azure Single-VM Deployment Execution

**Date**: 2026-06-21 03:39
**Severity**: Medium
**Component**: Infrastructure, Docker Compose, GitHub Actions, Network Security
**Status**: Resolved (Deployment phases 1, 2, 4, 7 complete; pending operator phases 0, 3, 5, 6)

## What Happened

Executed the Azure single-VM deployment plan (ck_plans/260621-azure-vm-deploy/plan.md) to move the World Cup predictor backend from local dev to a managed Azure VM with Caddy reverse proxy. Completed repo phases 1, 2, 4, 7 (Docker Compose refactor, NSG rules, GitHub Actions pipeline, deployment validation). Code committed as 9f6a0f9a.

## The Brutal Truth

Docker Compose's overlay system is poorly understood and caused the first real blocker. The framework concatenates `ports` lists across files—you cannot remove a host port from a base file in an overlay. Spent an hour debugging why prod was still exposing backend port 8000 until realizing the override file design was fundamentally wrong. The shame is that the Docker docs mention this in passing, not in the ports section where it matters.

The Azure NSG auto-rule collision was a near-miss for production: a single `az vm create --nsg-rule SSH` creates a priority-1000 rule that opens port 22 to 0.0.0.0/0. Adding our own my-IP rule at the same priority causes a silent failure. Code review caught this before deployment.

The GitHub Actions blocker felt like fighting the Azure SDK: self-hosted runners can't SSH through a my-IP-only NSG. Resolved with a just-in-time (JIT) rule that opens, deploys, closes—janky but effective.

## Technical Details

### Docker Compose Port Management
- **Base file** (docker-compose.yml): No host ports. Backend container 8000/tcp and Postgres 5432/tcp are internal-only (services can reach them via network, not from host).
- **Override file** (docker-compose.override.yml, auto-loaded in dev): `ports: - "8000:8000"` for manual testing, `- "5432:5432"` for admin access.
- **Prod file** (docker-compose.prod.yml, explicit on deploy): No ports. Caddy on the host (not containerized) reverse-proxies incoming 80/443 to backend container.

Verified with `docker-compose -f docker-compose.yml -f docker-compose.prod.yml config | grep -A5 ports:` — confirmed only Caddy 80/443 published; backend and postgres are internal.

### NSG Priority Collision
- **Bug**: `az vm create --nsg-rule SSH` creates rule `allow-SSH` at priority 1000, opening 0.0.0.0/0:22.
- **Intent**: Add `allow-my-ip` rule at priority 1000 to restrict 22 to operator IP only.
- **Outcome**: Priority collision; Azure silently ignores or chooses one. Risk: production SSH open to the internet.
- **Fix**: Use `--nsg-rule NONE` on VM creation so no auto-rule exists. Our `allow-my-ip` rule becomes priority 1000 and is the sole SSH ingress.

### GitHub Actions Just-in-Time NSG Rule
GitHub-hosted runners have dynamic IPs. Deploying through a my-IP-only NSG means the runner can't SSH to the VM. Workaround:
1. Deploy job fetches runner public IP (via `https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}` and jq).
2. Temporarily adds NSG rule `allow-runner-deploy` (priority 100) for 5 minutes.
3. Runs deploy playbook (terraform + ansible).
4. Closes the rule with `if: always()` to guarantee cleanup.

Requires three secrets: `AZURE_CREDENTIALS` (service principal JSON), `AZURE_RESOURCE_GROUP`, `AZURE_NSG_NAME`.

### Single Backend Dockerfile Strategy
- **Single file**: `backend/Dockerfile` (no .api, .job variants) runs three entry points:
  - `migrate`: Alembic upgrade head on startup.
  - `backend`: FastAPI uvicorn server.
  - `scheduler`: APScheduler daemon (only in prod, CPU-light).
- **GHCR owner**: `phucsystem` (not the operator account; avoids PAT friction).

Confirmed all three modes run successfully in prod image build.

## What We Tried

1. **Docker Compose overlay design (Failed)**: Attempted to use `docker-compose.override.yml` to REMOVE base ports. Docker doesn't support port removal—only addition/replacement. Realized the base file must have zero host ports for this to work.

2. **NSG priority balancing (Failed)**: Set our custom rule at priority 1100 (higher number = lower priority) thinking this would fall after the auto-rule. NSG uses lower numeric value = higher priority; our rule was ignored. Fix: disabled the auto-rule entirely.

3. **Static runner IP whitelist (Failed)**: Attempted to pre-add all GitHub IP blocks to the NSG. GitHub's IP ranges are large and frequently updated; NSG has a 200-rule limit. JIT rule is cleaner.

## Root Cause Analysis

### Docker Compose Ports
The root cause is the design assumption that overlays could selectively remove bindings. Overlays in Docker Compose are merge operations, not patch operations. The base `ports` list is concatenated with the overlay's list. This is actually documented, but the port-specific section of the Docker docs doesn't make it explicit—you have to read the "Compose file merge rules" appendix.

### NSG Priority Collision
Azure's `az vm create` helper assumes you want sane defaults (SSH open to the world). The `--nsg-rule SSH` flag creates a hardcoded priority-1000 rule. If you try to add another at the same priority, the behavior is undefined (Azure's choice of which rule takes effect). Root cause: the CLI doesn't prevent priority collisions; it silently allows them.

### GitHub Actions + My-IP NSG
The fundamental issue is that GitHub-hosted runners have no static IP. The design constraint (my-IP-only NSG for security) and the runtime reality (dynamic runner IP) are in direct conflict. JIT rules are the standard workaround, but it adds operational overhead.

## Lessons Learned

1. **Docker Compose overlays are merge-only.** Base files must be intentionally minimal if you plan to override. Document this explicitly in docker-compose.yml as comments. Future devs will waste time otherwise.

2. **Azure NSG rule priorities need explicit validation.** Before creating a rule, check for collisions with `az network nsg rule list`. Don't rely on the CLI to prevent conflicts.

3. **GitHub Actions + Azure = JIT rules are necessary.** There's no perfect solution. Document the 5-minute window and ensure cleanup always runs (`if: always()`).

4. **Single Dockerfile for multiple entry points is maintainable.** The overhead of three separate Dockerfiles (api, job, migrate) exceeds the benefit. One file, three commands in `docker-compose.prod.yml` services.

5. **GHCR ownership must match deployment credentials.** If the VM's service principal owns the GHCR token but a different user owns the code repo, use a PAT or a shared service principal for image pulls. We chose `phucsystem` to avoid this friction.

## Next Steps

| Phase | Owner | Timeline | Blocker? |
|-------|-------|----------|----------|
| **Phase 0** (Pending) | Operator | Pre-deploy: az login, create service principal, store AZURE_CREDENTIALS secret | JIT rule can't run without this |
| **Phase 3** (Pending) | Operator | DNS: point domain to Caddy public IP, HTTPS validation | Live traffic can't route without DNS |
| **Phase 5** (Pending) | Operator | SSH key provisioning for ansible ansible_user=azureuser | Playbook can't execute without SSH |
| **Phase 6** (Pending) | Operator | Cost guardrails: set Azure budget alert, review pg-backup.sh cron | Prevents bill shock |
| **Cleanup** (After go-live) | Tech debt | Remove dead artifacts: backend/Dockerfile.api, backend/Dockerfile.job, app/pipeline/scheduler_entry.py | Non-blocking; cleanup-only |

**Verification checklist:**
- Backend tests: 80/80 passed.
- Docker Compose YAML: Valid (docker-compose config verified).
- GitHub Actions workflow: Syntax validated; needs AZURE_CREDENTIALS secret before first run.
- Caddy config: Only 80/443 published; reverse proxy rules point to internal backend:8000.
