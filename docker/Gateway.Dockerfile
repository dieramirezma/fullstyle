FROM node:22.23.4-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da
RUN npm install --global pnpm@10.8.1
WORKDIR /app
COPY FullStyle-API-Gateway/package.json FullStyle-API-Gateway/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts
COPY FullStyle-API-Gateway .
RUN pnpm run lint && pnpm run format:check && pnpm run build && node --test tests/chat-delegation.cjs
ENV NODE_ENV=production
USER node
CMD ["node", "dist/index.js"]
