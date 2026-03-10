FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

RUN npm prune --omit=dev

ENV NODE_ENV=production
EXPOSE 3010
CMD ["npm", "start"]