# Etapa 1: Build de TypeScript
FROM node:20 AS builder

WORKDIR /app

# Copiar archivos esenciales
COPY package.json pnpm-lock.yaml ./
COPY tsconfig.json ./

# Copiar el código fuente
COPY ./src ./src


# Instalar dependencias y compilar
RUN npm install -g pnpm && pnpm install
RUN pnpm build

# Copiar los esquemas GraphQL directamente (no dentro de src en prod)
COPY ./src/graphql/schemas ./dist/graphql/schemas

# Etapa 2: Imagen final para producción
FROM node:20-slim

WORKDIR /app

# Copiar solo lo necesario desde la etapa de build
COPY --from=builder /app/package.json /app/pnpm-lock.yaml ./
COPY --from=builder /app/dist ./dist

# Instalar solo dependencias de producción
RUN npm install -g pnpm && pnpm install --prod

# Exponer el puerto (ajusta si usas otro)
EXPOSE 4000

# Comando de inicio
CMD ["node", "dist/src/index.js"]
