FROM node:22-alpine AS build
WORKDIR /app
COPY apps/api/package.json apps/api/tsconfig.json ./
COPY packages/shared-schemas /packages/shared-schemas
COPY apps/api/src ./src
RUN npm install --ignore-scripts

FROM node:22-alpine
WORKDIR /app
COPY --from=build /app /app
COPY --from=build /packages/shared-schemas /packages/shared-schemas
ENV NODE_ENV=production
EXPOSE 8080
USER node
CMD ["npm", "start"]
