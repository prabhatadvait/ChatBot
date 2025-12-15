FROM node:18-alpine

WORKDIR /app

# Copy package.json + lock file
COPY package*.json ./

# Install dependencies
RUN npm install --omit=dev

# Copy rest of the frontend code
COPY . .

# Build Next.js app
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]






# # ---------- builder ----------
# FROM node:18-alpine AS builder

# WORKDIR /app

# COPY package*.json ./
# RUN npm install --omit=dev

# COPY . .
# RUN npm run build

# # ---------- runtime ----------
# FROM nginx:alpine

# COPY --from=builder /app/.next /usr/share/nginx/html/.next
# COPY --from=builder /app/pages /usr/share/nginx/html/pages
# COPY --from=builder /app/package.json /usr/share/nginx/html/package.json

# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]
