FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY package.json ./
RUN npm install --omit=dev --ignore-scripts && npm cache clean --force

COPY . .
RUN mkdir -p /app/audit \
  && chown -R node:node /app \
  && chmod 700 /app/audit

USER node
EXPOSE 3001
CMD ["node", "src/index.js"]
