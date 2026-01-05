# שלב 1: בנייה
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# שלב 2: הגשה (Serving) עם שרת קליל
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# הגדרת פורט (Nginx רץ על 80 כברירת מחדל)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]