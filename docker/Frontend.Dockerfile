FROM node:22.23.4-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da
WORKDIR /app
COPY FullStyle-Frontend/package.json FullStyle-Frontend/package-lock.json ./
RUN --mount=type=cache,id=fullstyle-portfolio-npm-frontend,target=/root/.npm npm ci --ignore-scripts --no-audit --no-fund
COPY FullStyle-Frontend .
ENV NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_API_URL=/api/logic/ NEXT_PUBLIC_APP_URL=http://localhost:38080
RUN npm test && npm run lint && npm run typecheck && npm run build && node scripts/prepare-standalone.cjs
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
CMD ["node", ".next/standalone/server.js"]
