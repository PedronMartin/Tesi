FROM node:20-alpine as builder

WORKDIR /app

#dipendenze
COPY package*.json ./
RUN npm install
COPY . .

#compilazione angular
RUN npm run build

#esecuzione tramite Nginx
FROM nginx:alpine

#file di configurazione custom Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist/greenratingalgorithm/browser /usr/share/nginx/html

#Nginx usa la porta 80 di default
EXPOSE 80