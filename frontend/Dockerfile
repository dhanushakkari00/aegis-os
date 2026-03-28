FROM node:22-alpine

WORKDIR /app

ENV PORT=8080

COPY package.json /app/package.json
RUN npm install

COPY . /app

RUN npm run build

EXPOSE 8080

CMD ["sh", "-c", "npm run start -- --hostname 0.0.0.0 --port ${PORT}"]
