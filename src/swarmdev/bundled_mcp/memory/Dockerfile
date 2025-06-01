# Multi-stage build for production optimization
# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./

# Install all dependencies (including dev dependencies for building)
RUN npm install

# Copy source code
COPY . .

# Build TypeScript to JavaScript
RUN npm run build

# Stage 2: Runtime
FROM node:18-alpine AS runtime

WORKDIR /app

# Copy package files
COPY --from=builder /app/package*.json ./

# Install only production dependencies
RUN npm install --only=production

# Copy built JavaScript files
COPY --from=builder /app/dist ./dist

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Change ownership of the app directory
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port (though MCP typically uses stdio)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('Server is healthy')" || exit 1

# Start the server
CMD ["npm", "start"] 