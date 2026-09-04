# ---------- Build (Vite) ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# URLs de los servicios: se inyectan en tiempo de build (Vite las incrusta en el bundle)
ARG VITE_REST_BASE_URL
ARG VITE_AUTH_BASE_URL
ARG VITE_GRAPHQL_URL
ARG VITE_WS_URL
ARG VITE_AI_SERVICE_URL
ARG VITE_PAYMENT_BASE_URL
ENV VITE_REST_BASE_URL=$VITE_REST_BASE_URL \
    VITE_AUTH_BASE_URL=$VITE_AUTH_BASE_URL \
    VITE_GRAPHQL_URL=$VITE_GRAPHQL_URL \
    VITE_WS_URL=$VITE_WS_URL \
    VITE_AI_SERVICE_URL=$VITE_AI_SERVICE_URL \
    VITE_PAYMENT_BASE_URL=$VITE_PAYMENT_BASE_URL

RUN npm run build

# ---------- Runtime (Nginx) ----------
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
