# syntax=docker/dockerfile:1

# --- Builder ---
FROM node:24-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# --- Dev (hot reload) ---
# Used only by docker-compose.override.yml. Source is bind-mounted over /app at
# runtime; node_modules here (linux/musl) is kept alive by an anonymous volume so
# the host's darwin node_modules never shadows it. `next dev` defaults to
# Turbopack, which picks up bind-mount changes via Docker Desktop file sharing.
# WATCHPACK_POLLING is the polling fallback only if you switch to `--webpack`.
FROM node:24-alpine AS dev
WORKDIR /app

ENV NODE_ENV=development \
    PORT=3000 \
    WATCHPACK_POLLING=true

COPY package.json package-lock.json* ./
RUN npm ci

EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- Runner ---
FROM node:24-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# next standalone output bundles server + node_modules subset
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
