#!/usr/bin/env bash
# Phase 3 — provision the single VM (idempotent-ish; safe to re-run for missing bits).
# Creates the resource group, a burstable Ubuntu VM with Docker (via cloud-init), and
# an NSG that allows 80/443 from anywhere and 22 only from your current public IP.
# Default size is an amd64 v2 burstable SKU (gen1 B-series like B1ms/B2s is often
# NotAvailableForSubscription). Avoid ARM (B*p*) SKUs — CI builds amd64 images.
#
# Run on your LOCAL machine where `az login` is done — NOT on the VM.
# Usage: ./infra/provision-vm.sh
# Override defaults via env: RG, LOCATION, VM_NAME, VM_SIZE, ADMIN_USER, SPOT=1
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
LOCATION="${LOCATION:-australiaeast}"
VM_NAME="${VM_NAME:-vm-wc2026}"
VM_SIZE="${VM_SIZE:-Standard_B2als_v2}"
ADMIN_USER="${ADMIN_USER:-azureuser}"
IMAGE="${IMAGE:-Ubuntu2204}"
DISK_GB="${DISK_GB:-30}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v az >/dev/null || { echo "az CLI not found — run this on your LOCAL machine (where 'az login' is done), not the VM." >&2; exit 1; }
az account show >/dev/null 2>&1 || { echo "Run 'az login' first." >&2; exit 1; }

MY_IP="$(curl -fsS https://api.ipify.org)"

# Preflight: fail fast with guidance if the SKU is restricted here, instead of
# letting `az vm create` throw an opaque SkuNotAvailable deep in a traceback.
RESTRICTION="$(az vm list-skus -l "$LOCATION" --resource-type virtualMachines --all \
  --query "[?name=='$VM_SIZE'].restrictions[].reasonCode" -o tsv 2>/dev/null)"
if [[ -n "$RESTRICTION" ]]; then
  echo "ERROR: VM size $VM_SIZE is not available in $LOCATION ($RESTRICTION)." >&2
  echo "Available amd64 burstable sizes here:" >&2
  az vm list-skus -l "$LOCATION" --resource-type virtualMachines --all \
    --query "[?starts_with(name,'Standard_B') && !contains(name,'p') && length(restrictions)==\`0\`].{Name:name, vCPU:capabilities[?name=='vCPUs']|[0].value, MemGB:capabilities[?name=='MemoryGB']|[0].value}" \
    -o table >&2
  echo "Re-run with e.g.: VM_SIZE=Standard_B2als_v2 ./infra/provision-vm.sh" >&2
  exit 1
fi

echo ">> Provisioning $VM_NAME ($VM_SIZE) in $RG / $LOCATION; SSH locked to $MY_IP"

az group create -n "$RG" -l "$LOCATION" -o none

SPOT_ARGS=()
if [[ "${SPOT:-0}" == "1" ]]; then
  SPOT_ARGS=(--priority Spot --eviction-policy Deallocate --max-price -1)
  echo ">> Spot enabled (eviction: Deallocate)"
fi

# Capture output so a QuotaExceeded/SkuNotAvailable ARM error surfaces as a clear
# message instead of azure-cli's raw Python traceback (it crashes formatting it).
VM_LOG="$(mktemp)"; trap 'rm -f "$VM_LOG"' EXIT
if ! az vm create \
  -g "$RG" -n "$VM_NAME" \
  --image "$IMAGE" --size "$VM_SIZE" \
  --admin-username "$ADMIN_USER" \
  --generate-ssh-keys \
  --os-disk-size-gb "$DISK_GB" \
  --storage-sku StandardSSD_LRS \
  --custom-data "$HERE/cloud-init.yaml" \
  --public-ip-sku Standard \
  --nsg-rule NONE \
  ${SPOT_ARGS[@]+"${SPOT_ARGS[@]}"} \
  -o table 2>&1 | tee "$VM_LOG"; then
  echo "" >&2
  if grep -q QuotaExceeded "$VM_LOG"; then
    echo "ERROR: vCPU quota for $VM_SIZE's family is 0 in $LOCATION." >&2
    echo "Request an increase: Azure Portal → Quotas → Compute → region '$LOCATION'" >&2
    echo "→ search the VM family (e.g. 'Bsv2'/'Basv2') → New quota → 4. Re-run after approval." >&2
    echo "Or try another region: LOCATION=<region> ./infra/provision-vm.sh" >&2
  elif grep -q SkuNotAvailable "$VM_LOG"; then
    echo "ERROR: $VM_SIZE is not available in $LOCATION. Re-run with VM_SIZE=... or LOCATION=..." >&2
  else
    echo "ERROR: az vm create failed. Last lines:" >&2
    tail -15 "$VM_LOG" >&2
  fi
  exit 1
fi

# NONE above means the auto-created NSG has no inbound allow rules; we add exactly
# the ones we want. SSH is locked to your current IP (the ONLY port-22 rule).
az network nsg rule create -g "$RG" --nsg-name "${VM_NAME}NSG" \
  -n allow-ssh-myip --priority 1000 --access Allow --protocol Tcp \
  --direction Inbound --destination-port-ranges 22 \
  --source-address-prefixes "${MY_IP}/32" -o none
az network nsg rule create -g "$RG" --nsg-name "${VM_NAME}NSG" \
  -n allow-web --priority 1010 --access Allow --protocol Tcp \
  --direction Inbound --destination-port-ranges 80 443 \
  --source-address-prefixes Internet -o none

PUBLIC_IP="$(az vm show -d -g "$RG" -n "$VM_NAME" --query publicIps -o tsv)"
echo ""
echo ">> VM ready. Public IP: $PUBLIC_IP"
echo ">> Next:"
echo "   1. Point your DNS A record (or use ${PUBLIC_IP//./-}.sslip.io) at $PUBLIC_IP"
echo "   2. ssh ${ADMIN_USER}@${PUBLIC_IP}"
echo "   3. git clone the repo, create .env (see docs/deployment.md), then run the deploy workflow"
echo "   4. GitHub secrets: SSH_HOST=$PUBLIC_IP  SSH_USER=$ADMIN_USER  SSH_PRIVATE_KEY=~/.ssh/id_rsa"
