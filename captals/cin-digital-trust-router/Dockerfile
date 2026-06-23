FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY . .
RUN mkdir -p /app/audit && chown -R node:node /app

USER node
EXPOSE 3001
CMD ["node", "src/index.js"]
