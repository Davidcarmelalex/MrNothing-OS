import java.io.File
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
        testInstrumentationRunner = "android.test.InstrumentationTestRunner"
        // Avoid the legacy runner's whole-APK DexFile package scan during startup.
        // The exact class inventory is source-gated in tests/test_qa005_workflow_gate.py.
        testInstrumentationRunnerArguments["class"] = listOf(
            "tech.mrnothing.os.AccessibilityDisclosureActivityTest",
            "tech.mrnothing.os.MemoryVaultManifestBoundaryTest",
            "tech.mrnothing.os.AgentPlanPreviewActivityTest",
            "tech.mrnothing.os.AndroidAtomicAuthorityRecordPersistenceTest",
            "tech.mrnothing.os.AndroidAuthorityTrustCryptoFailureModeTest",
            "tech.mrnothing.os.OwnerAuthorityTrustActivityCommitLifecycleTest",
            "tech.mrnothing.os.OwnerAuthorityTrustActivityLifecycleTest",
            "tech.mrnothing.os.MemoryVaultKeySpecContractTest"
        ).joinToString(",")
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

val androidTestPlatformApiJars = listOf(
    "android.test.base.jar",
    "android.test.runner.jar"
).map { name ->
    File(android.sdkDirectory, "platforms/android-35/optional/$name").also { jar ->
        check(jar.isFile) { "Missing Android SDK optional test API: ${jar.path}" }
    }
}

dependencies {
    // Explicit, pinned software provider for portable Ed25519 SPKI import and signature verification.
    implementation("org.bouncycastle:bcprov-jdk18on:1.86")
    testImplementation("junit:junit:4.13.2")
    // Compile-only: the emulator supplies these platform test APIs at runtime.
    // Do not package deprecated android.test libraries into the app or test APK.
    androidTestCompileOnly(files(androidTestPlatformApiJars))
}


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


// CI-004C: derive release identity from the actual AGP release variant.
val releaseVariantApplicationId = objects.property<String>()
val releaseVariantName = objects.property<String>()
var releaseVariantCount = 0

androidComponents {
    onVariants(selector().withBuildType("release")) { variant ->
        releaseVariantCount += 1
        check(releaseVariantCount == 1) {
            "CI-003 requires exactly one release variant; review flavor identity policy before adding more"
        }
        releaseVariantApplicationId.set(variant.applicationId)
        releaseVariantName.set(variant.name)
    }
}

tasks.register("writeReleaseVariantMetadata") {
    val metadataFile = layout.buildDirectory.file("reports/ci003/release-variant-metadata.json")
    inputs.property("applicationId", releaseVariantApplicationId)
    inputs.property("variantName", releaseVariantName)
    outputs.file(metadataFile)
    doLast {
        val applicationId = releaseVariantApplicationId.get()
        val variantName = releaseVariantName.get()
        val segments = applicationId.split('.')
        val validApplicationId = segments.size >= 2 && segments.all { segment ->
            segment.isNotEmpty() &&
                (segment[0] in 'A'..'Z' || segment[0] in 'a'..'z') &&
                segment.all { character ->
                    character in 'A'..'Z' || character in 'a'..'z' ||
                        character in '0'..'9' || character == '_'
                }
        }
        require(validApplicationId) { "Gradle release variant produced an invalid applicationId" }
        require(variantName == "release") {
            "CI-003 currently accepts only the single unflavored release variant"
        }
        val output = metadataFile.get().asFile
        output.parentFile.mkdirs()
        output.writeText(
            """{"schema":"mrnothing-gradle-release-variant-v1","applicationId":"$applicationId","variantName":"$variantName","buildType":"release"}""" + "\n",
            Charsets.UTF_8
        )
    }
}
