FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

ENV TZ=Etc/GMT
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone
# Install gettext-commons for envsubst
RUN apk add --no-cache gettext

COPY --from=build /app/build /usr/share/nginx/html
# Copy the template, not the final config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]