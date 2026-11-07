#!/usr/bin/env python3
"""Prove Gradle strict dependency verification rejects a tampered Maven artifact.

Runs only against a disposable local Maven repository and temporary Gradle project.
No network repository, project dependency cache, device, signing key or production
credential is used by this negative control.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def jar_bytes(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        entry = zipfile.ZipInfo("payload.txt", date_time=(1980, 1, 1, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        entry.compress_type = zipfile.ZIP_STORED
        archive.writestr(entry, payload)
    return buffer.getvalue()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_module(repo: Path, name: str, actual_payload: bytes, expected_payload: bytes) -> tuple[str, str]:
    version_dir = repo / "com" / "example" / name / "1.0"
    version_dir.mkdir(parents=True, exist_ok=True)
    pom = (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<modelVersion>4.0.0</modelVersion>"
        "<groupId>com.example</groupId>"
        f"<artifactId>{name}</artifactId>"
        "<version>1.0</version>"
        "</project>\n"
    ).encode("utf-8")
    actual_jar = jar_bytes(actual_payload)
    expected_jar = jar_bytes(expected_payload)
    (version_dir / f"{name}-1.0.pom").write_bytes(pom)
    (version_dir / f"{name}-1.0.jar").write_bytes(actual_jar)
    return sha256(expected_jar), sha256(pom)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ci005_dependency_verification_negative.py /path/to/gradle", file=sys.stderr)
        return 2
    gradle = Path(sys.argv[1]).resolve()
    if not gradle.is_file() or not os.access(gradle, os.X_OK):
        print(f"Gradle executable is unavailable: {gradle}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="mrnothing-ci005-") as temporary:
        root = Path(temporary)
        project = root / "project"
        repo = project / "repo"
        verification = project / "gradle" / "verification-metadata.xml"
        project.mkdir()
        valid_jar, valid_pom = write_module(repo, "valid", b"known-good", b"known-good")
        tampered_jar, tampered_pom = write_module(repo, "tampered", b"modified", b"known-good")

        components = []
        for name, jar_hash, pom_hash in (
            ("valid", valid_jar, valid_pom),
            ("tampered", tampered_jar, tampered_pom),
        ):
            components.append(
                f'''      <component group="com.example" name="{name}" version="1.0">
         <artifact name="{name}-1.0.jar"><sha256 value="{jar_hash}"/></artifact>
         <artifact name="{name}-1.0.pom"><sha256 value="{pom_hash}"/></artifact>
      </component>'''
            )
        verification.parent.mkdir(parents=True)
        verification.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<verification-metadata xmlns="https://schema.gradle.org/dependency-verification">\n'
            "  <configuration><verify-metadata>true</verify-metadata>"
            "<verify-signatures>false</verify-signatures></configuration>\n"
            "  <components>\n" + "\n".join(components) +
            "\n  </components>\n</verification-metadata>\n",
            encoding="utf-8",
        )
        (project / "build.gradle").write_text(
            """repositories { maven { url = uri("$rootDir/repo") } }
configurations { validProbe; tamperedProbe }
dependencies {
    validProbe 'com.example:valid:1.0'
    tamperedProbe 'com.example:tampered:1.0'
}
tasks.register('verifyValidDependency') {
    doLast { configurations.validProbe.resolve() }
}
tasks.register('verifyTamperedDependency') {
    doLast { configurations.tamperedProbe.resolve() }
}
""",
            encoding="utf-8",
        )

        environment = os.environ.copy()
        environment["GRADLE_USER_HOME"] = str(root / "gradle-home")
        base = [
            str(gradle), "--no-daemon", "--offline",
            "--dependency-verification=strict", "-p", str(project),
        ]
        valid = subprocess.run(
            base + ["verifyValidDependency"], text=True, capture_output=True,
            env=environment, check=False,
        )
        if valid.returncode != 0:
            print(valid.stdout, file=sys.stderr)
            print(valid.stderr, file=sys.stderr)
            raise RuntimeError("strict verification rejected the valid positive-control artifact")

        tampered = subprocess.run(
            base + ["verifyTamperedDependency"], text=True, capture_output=True,
            env=environment, check=False,
        )
        combined = (tampered.stdout + "\n" + tampered.stderr).lower()
        if tampered.returncode == 0:
            raise RuntimeError("strict verification accepted a modified dependency artifact")
        if "tampered-1.0.jar" not in combined or "verification" not in combined:
            print(tampered.stdout, file=sys.stderr)
            print(tampered.stderr, file=sys.stderr)
            raise RuntimeError("Gradle failed for a reason other than dependency verification")

    print("CI-005 negative control passed: valid artifact accepted; modified artifact rejected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
