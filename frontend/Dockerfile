FROM node:22-alpine AS runner
WORKDIR /app

# Install dependencies first (for build caching)
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code and build production pages
COPY . .
RUN npm run build

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Run next server in production mode
CMD ["npm", "run", "start"]
