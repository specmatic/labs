rootProject.name = "specmatic-workshop-labs"

val excludedDirs = setOf(
    ".git",
    ".github",
    ".gradle",
    "build",
    "gradle",
    "out"
)

rootDir
    .listFiles()
    ?.filter { it.isDirectory && !it.name.startsWith(".") && it.name !in excludedDirs }
    ?.sortedBy { it.name }
    ?.forEach { labDir ->
        include(":${labDir.name}")
        project(":${labDir.name}").projectDir = labDir
    }
