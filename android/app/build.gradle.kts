import java.security.MessageDigest

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "tech.mrnothing.os"
    compileSdk = 35
    defaultConfig {
        applicationId = "tech.mrnothing.os"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-dev"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies { testImplementation("junit:junit:4.13.2") }


// CI-003: intentionally unsigned release output plus resolved runtime inventory.
android {
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
}

tasks.register("writeReleaseRuntimeInventory") {
    val inventoryFile = layout.buildDirectory.file("reports/ci003/release-runtime-dependencies.tsv")
    outputs.file(inventoryFile)
    doLast {
        val rows = configurations.getByName("releaseRuntimeClasspath").resolvedConfiguration.resolvedArtifacts.map { artifact ->
            val id = artifact.moduleVersion.id
            val digest = MessageDigest.getInstance("SHA-256")
            artifact.file.inputStream().use { input ->
                val buffer = ByteArray(8192)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    digest.update(buffer, 0, count)
                }
            }
            val hex = digest.digest().joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) }
            listOf(id.group, artifact.name, id.version, artifact.file.name, hex).joinToString("\t")
        }.sorted()
        val output = inventoryFile.get().asFile
        output.parentFile.mkdirs()
        output.writeText(rows.joinToString("\n") + if (rows.isEmpty()) "" else "\n", Charsets.UTF_8)
    }
}
