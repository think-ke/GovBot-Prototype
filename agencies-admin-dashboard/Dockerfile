# File: agencies-admin-dashboard/Dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

COPY . .
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3010
CMD ["npm", "start"]