FROM node:20-alpine AS builder

ARG VITE_BASE=/fbse/
ARG VITE_API_BASE_URL=/fbse/api

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN VITE_BASE=${VITE_BASE} VITE_API_BASE_URL=${VITE_API_BASE_URL} npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
