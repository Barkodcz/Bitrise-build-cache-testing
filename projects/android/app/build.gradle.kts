plugins {
    kotlin("jvm")
    application
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:model"))
    implementation(project(":feature:leaf"))
}

application {
    mainClass.set("com.showcase.app.MainKt")
}

// AGP-style task alias so `./gradlew :app:assembleDebug` (what tools/run-gradle.sh invokes)
// works unmodified on this plain Kotlin/JVM module. `assemble` is the closest JVM-plugin
// equivalent to AGP's `assembleDebug` (it builds the jar + distribution artifacts).
tasks.register("assembleDebug") {
    group = "build"
    description = "Alias for `assemble` so AGP-style task paths used by tooling keep working."
    dependsOn("assemble")
}
