#!/usr/bin/env bash
# Phase 6 — $20/mo budget alert at 50/80/100%. Run after provisioning.
# Run on your LOCAL machine where `az login` is done — NOT on the VM (the VM has
# no Azure CLI). Usage: ALERT_EMAIL=you@example.com ./infra/cost-guardrails.sh
# (Budget CLI shape varies by az version; if it errors, set this in the portal:
#  Cost Management -> Budgets -> Add, scope = the resource group, amount = 20.)
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
AMOUNT="${AMOUNT:-20}"
NAME="${NAME:-budget-wc2026}"
ALERT_EMAIL="${ALERT_EMAIL:?set ALERT_EMAIL=you@example.com}"

command -v az >/dev/null || { echo "az CLI not found — run this on your LOCAL machine (where 'az login' is done), not the VM." >&2; exit 1; }
az account show >/dev/null 2>&1 || { echo "Run 'az login' first." >&2; exit 1; }

START="$(date +%Y-%m-01)"
END="2027-01-01"
ERR="$(mktemp)"; trap 'rm -f "$ERR"' EXIT

# The 'az consumption' group is in preview and often rejects RG-scoped budgets
# (API-version quirks). Attempt it; on failure, fall back to reliable portal steps.
if az consumption budget create \
  --budget-name "$NAME" \
  --amount "$AMOUNT" \
  --category Cost \
  --time-grain Monthly \
  --start-date "$START" \
  --end-date "$END" \
  --resource-group "$RG" \
  -o table 2>"$ERR"; then
  echo ">> Budget '$NAME' (\$$AMOUNT/mo) created on $RG."
  echo ">> Add 50/80/100% email alerts to $ALERT_EMAIL in the portal if not already set."
else
  echo "!! az couldn't create the budget (the 'consumption' CLI is preview/flaky):" >&2
  sed 's/^/   /' "$ERR" >&2
  echo "" >&2
  echo ">> Set it in the portal instead (2 min, reliable):" >&2
  echo "   Cost Management + Billing -> Budgets -> + Add" >&2
  echo "   Scope: resource group '$RG'   Amount: \$$AMOUNT/mo   Reset: Monthly" >&2
  echo "   Alerts: 50/80/100% -> $ALERT_EMAIL" >&2
fi
