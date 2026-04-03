# Stage 1: Build
FROM node:18-alpine AS builder
# Enable pnpm
RUN corepack enable && corepack prepare pnpm@9.0.0 --activate
WORKDIR /app
# We only copy the root workspace configs and the frontend app for building
COPY package.json pnpm-workspace.yaml turbo.json .npmrc ./
COPY apps/frontend ./apps/frontend
COPY packages ./packages

# Install dependencies for the monorepo root
RUN pnpm install

# Build the frontend using turbo
RUN pnpm --filter @bharatvoice/frontend build

# Stage 2: Serve
FROM nginx:alpine
# Copy built assets
COPY --from=builder /app/apps/frontend/dist /usr/share/nginx/html

# Write a basic nginx.conf inline to handle React Router internally (no need for a separate file)
RUN echo "server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files \$uri \$uri/ /index.html; \
    } \
}" > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
