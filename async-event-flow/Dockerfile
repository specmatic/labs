FROM eclipse-temurin:17.0.18_8-jre
WORKDIR /app
COPY build/libs/*.jar /app/app.jar
EXPOSE 8080 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
