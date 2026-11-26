plugins {
    kotlin("jvm")
    `java-library`
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(project(":core:common"))

    testImplementation(platform("org.junit:junit-bom:5.10.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
}

tasks.test {
    useJUnitPlatform()
}

// AGP-style task alias so `./gradlew :core:model:testDebugUnitTest` (what tools/run-gradle.sh
// invokes) works unmodified on this plain Kotlin/JVM module.
tasks.register("testDebugUnitTest") {
    group = "verification"
    description = "Alias for `test` so AGP-style task paths used by tooling keep working."
    dependsOn("test")
}
