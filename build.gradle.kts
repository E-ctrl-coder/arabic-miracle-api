import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    id("org.springframework.boot") version "3.2.5"
    id("io.spring.dependency-management") version "1.1.4"
    kotlin("jvm") version "1.9.23"
    kotlin("plugin.spring") version "1.9.23"
}

group = "com.arabicanalyzer"
version = "0.1.0"

java {
    sourceCompatibility = JavaVersion.VERSION_17
}

// Define dependency versions directly
val openaiJavaVersion = "0.21.0" // Official OpenAI Java library version
val luceneVersion = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    // Spring Boot
    implementation("org.springframework.boot:spring-boot-starter-web")
    // --- FIX: Add the WebFlux starter to include the full reactive stack ---
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    implementation("org.jetbrains.kotlin:kotlin-reflect")

    // --- FIX: Add the coroutines-reactor bridge ---
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor")

    implementation("com.openai:openai-java:$openaiJavaVersion")

    // Lucene Arabic Analyzer
    implementation("com.github.msarhan:lucene-arabic-analyzer:$luceneVersion")

    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        freeCompilerArgs += "-Xjsr305=strict"
        jvmTarget = "17"
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}