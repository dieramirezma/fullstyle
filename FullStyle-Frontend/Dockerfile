# Etapa de construcción
FROM node:18-alpine AS builder

WORKDIR /app
COPY . .

# Pasar variables de entorno durante el build
ARG INSTANCE_ID
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_URL
ENV INSTANCE_ID=$INSTANCE_ID
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL

RUN npm install
RUN npm run build

# Etapa de producción (Next.js standalone mode)
FROM node:18-alpine

ENV NODE_ENV=production

WORKDIR /app

# Copiamos el output de Next.js standalone
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static

# Asegurar que las variables de entorno estén disponibles en runtime
ARG INSTANCE_ID
ENV INSTANCE_ID=$INSTANCE_ID

EXPOSE 3000
CMD ["node", "server.js"]
