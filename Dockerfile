# --- Stage 1: Build ---
# Use an official Gradle image with a JDK to build the application.
FROM gradle:8.5-jdk17 AS build

# Set the working directory
WORKDIR /home/gradle/project

# --- 1. Copy only the files needed for dependency resolution ---
# This creates a cached layer that is only invalidated when your build files change.
COPY build.gradle.kts gradle.properties ./
COPY gradle ./gradle
COPY gradlew ./

# Make the Gradle wrapper executable
RUN chmod +x ./gradlew

# --- 2. Download dependencies ---
# This step will be cached by Docker as long as the files above haven't changed.
RUN ./gradlew dependencies --no-daemon

# --- 3. Copy the rest of the source code ---
# This layer is invalidated more frequently (whenever you change a source file).
COPY src ./src

# --- 4. Build the application ---
# This final step uses the cached dependencies and re-compiles only your code.
RUN ./gradlew bootJar --no-daemon


# --- Stage 2: Run ---
# Use a lightweight JRE image for the final container.
FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

# Copy only the built JAR from the 'build' stage into the final image
COPY --from=build /home/gradle/project/build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]