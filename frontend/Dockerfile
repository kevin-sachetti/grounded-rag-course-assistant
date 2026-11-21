# 1) Compila a interface
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# No contêiner a API é acessada pelo mesmo endereço da página, em /api (ver nginx.conf).
ENV VITE_API_URL=/api
RUN npm run build

# 2) Serve os arquivos prontos
FROM nginx:1.28-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
