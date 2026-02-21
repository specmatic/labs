FROM eclipse-temurin:17-jdk AS build
WORKDIR /workspace

COPY gradlew gradlew.bat build.gradle ./
COPY gradle gradle
COPY gradle.properties ./
RUN chmod +x gradlew

# Resolve dependencies in a dedicated layer for better build cache reuse.
RUN ./gradlew -i --no-daemon dependencies

COPY src src
RUN ./gradlew -i --no-daemon clean bootJar -x test

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=build /workspace/build/libs/*.jar /app/app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
