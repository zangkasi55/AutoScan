FROM node:22-alpine AS build
WORKDIR /app
COPY apps/web/package.json apps/web/vite.config.ts apps/web/tsconfig.json apps/web/index.html ./
COPY apps/web/src ./src
COPY packages/i18n /packages/i18n
RUN npm install --ignore-scripts && npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
