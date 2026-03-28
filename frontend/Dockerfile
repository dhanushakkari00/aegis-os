FROM node:22-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL=
ARG INTERNAL_API_ORIGIN=http://127.0.0.1:8000
ENV PORT=8080
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV INTERNAL_API_ORIGIN=${INTERNAL_API_ORIGIN}

COPY package.json /app/package.json
RUN npm install

COPY . /app

RUN npm run build

EXPOSE 8080

CMD ["sh", "-c", "npm run start -- --hostname 0.0.0.0 --port ${PORT}"]
