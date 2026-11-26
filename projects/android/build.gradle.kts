// Root build file for the Android build-cache showcase (plain Kotlin/JVM, no Android SDK required).

plugins {
    kotlin("jvm") version "2.0.21" apply false
}

// Showcase hook (AND-B03 / AND-G01): a Gradle property passed via `-PshowcaseNs=<value>`.
// It is read here and logged; individual modules may use it to namespace generated code.
val showcaseNs: String? = project.findProperty("showcaseNs") as String?

if (showcaseNs != null) {
    logger.lifecycle("[showcase] showcaseNs property = $showcaseNs")
}

// Nice-to-have: wire showcaseNs into compile/test task inputs across all modules so the
// property actually participates in Gradle's up-to-date checks / build cache keys when set.
allprojects {
    tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
        inputs.property("showcaseNs", showcaseNs ?: "").optional(true)
    }
    tasks.withType<Test>().configureEach {
        inputs.property("showcaseNs", showcaseNs ?: "").optional(true)
    }
}
