# Stage 1: build the Angular app. Node and node_modules only exist in this stage.
FROM node:26-alpine AS build
WORKDIR /app
# Dependencies first, so this layer is reused until package-lock.json changes.
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx ng build

# Stage 2: the final image is just nginx plus the built static files.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
