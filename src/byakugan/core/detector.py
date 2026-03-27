"""Auto-detect project tech stack from files in the project root."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from byakugan.core.config import ProjectProfile


# Maps detected framework/lib → suggested template path (relative to templates/)
FRAMEWORK_TO_TEMPLATE: dict[str, str] = {
    # Python web
    "fastapi": "project-types/web-backend.md",
    "starlette": "project-types/web-backend.md",
    "django": "project-types/web-backend.md",
    "flask": "project-types/web-backend.md",
    "aiohttp": "project-types/web-backend.md",
    "tornado": "project-types/web-backend.md",
    "litestar": "project-types/web-backend.md",
    # Python ML
    "torch": "project-types/ml-project.md",
    "tensorflow": "project-types/ml-project.md",
    "jax": "project-types/ml-project.md",
    "sklearn": "project-types/ml-project.md",
    "scikit-learn": "project-types/ml-project.md",
    "xgboost": "project-types/ml-project.md",
    "lightgbm": "project-types/ml-project.md",
    # Python LLM
    "langchain": "project-types/llm-project.md",
    "openai": "project-types/llm-project.md",
    "anthropic": "project-types/llm-project.md",
    "llama-index": "project-types/llm-project.md",
    "llama_index": "project-types/llm-project.md",
    "instructor": "project-types/llm-project.md",
    "litellm": "project-types/llm-project.md",
    # JS/TS fullstack
    "next": "project-types/fullstack-web.md",
    "nuxt": "project-types/fullstack-web.md",
    "remix": "project-types/fullstack-web.md",
    "sveltekit": "project-types/fullstack-web.md",
    # JS/TS frontend
    "react": "project-types/web-frontend.md",
    "vue": "project-types/web-frontend.md",
    "svelte": "project-types/web-frontend.md",
    "solid-js": "project-types/web-frontend.md",
    "angular": "project-types/web-frontend.md",
    # JS/TS backend
    "express": "project-types/web-backend.md",
    "fastify": "project-types/web-backend.md",
    "hono": "project-types/web-backend.md",
    "koa": "project-types/web-backend.md",
    "nestjs": "project-types/web-backend.md",
    "elysia": "project-types/web-backend.md",
}

LANGUAGE_TO_TEMPLATE: dict[str, str] = {
    "python": "languages/python.md",
    "typescript": "languages/typescript.md",
    "javascript": "languages/javascript.md",
    "rust": "languages/rust.md",
    "go": "languages/go.md",
    "java": "languages/java.md",
    "kotlin": "languages/kotlin.md",
    "swift": "languages/swift.md",
    "ruby": "languages/ruby.md",
    "php": "languages/php.md",
    "c": "languages/c.md",
    "cpp": "languages/cpp.md",
    "css": "languages/css.md",
}

# Templates always suggested when their domain is detected
ALWAYS_SUGGEST: dict[str, list[str]] = {
    "web-backend": ["specialized/security-check.md", "specialized/api-design.md"],
    "api-service": ["specialized/security-check.md", "specialized/api-design.md"],
    "fullstack-web": ["specialized/security-check.md"],
    "web-frontend": [],
    "ml-project": [],
    "llm-project": ["specialized/security-check.md"],
    "mobile-app": [],
    "library-sdk": [],
    "cli-tool": [],
    "desktop-app": [],
    "data-engineering": [],
    "devops-infrastructure": ["specialized/security-check.md"],
}


class DetectionResult:
    def __init__(self) -> None:
        self.profile = ProjectProfile()
        self.suggested_templates: list[str] = []
        self.confidence: dict[str, str] = {}  # template → "detected" | "inferred"

    def add_template(self, template: str, how: str = "detected") -> None:
        if template not in self.suggested_templates:
            self.suggested_templates.append(template)
            self.confidence[template] = how


def detect(root: Path) -> DetectionResult:
    result = DetectionResult()
    profile = result.profile
    profile.name = root.name

    _detect_python(root, result)
    _detect_javascript(root, result)
    _detect_rust(root, result)
    _detect_go(root, result)
    _detect_java(root, result)
    _detect_ruby(root, result)
    _detect_php(root, result)
    _detect_swift(root, result)
    _detect_c_cpp(root, result)

    # Infer project type from presence of certain files if not yet detected
    _infer_project_type(root, result)

    # Add specialized templates based on project types detected
    for pt in profile.project_types:
        pt_key = pt.replace("project-types/", "").replace(".md", "")
        for spec in ALWAYS_SUGGEST.get(pt_key, []):
            result.add_template(spec, "inferred")

    # Always suggest testing and database if we have a backend
    if any("backend" in t or "fullstack" in t for t in profile.project_types):
        result.add_template("specialized/testing-strategy.md", "inferred")
        result.add_template("specialized/database-design.md", "inferred")

    return result


# ── Language detectors ────────────────────────────────────────────────────────

def _detect_python(root: Path, result: DetectionResult) -> None:
    profile = result.profile
    indicators = [
        root / "pyproject.toml",
        root / "setup.py",
        root / "setup.cfg",
        root / "requirements.txt",
        root / "uv.lock",
        root / "poetry.lock",
    ]
    if not any(p.exists() for p in indicators) and not list(root.glob("*.py")):
        return

    profile.languages.append("python")
    result.add_template(LANGUAGE_TO_TEMPLATE["python"])

    # Python version
    if (root / ".python-version").exists():
        profile.python_version = (root / ".python-version").read_text().strip()
    elif (root / "pyproject.toml").exists():
        try:
            with open(root / "pyproject.toml", "rb") as f:
                data = tomllib.load(f)
            req = data.get("project", {}).get("requires-python", "")
            if req:
                profile.python_version = req.lstrip(">=<~^")
        except Exception:
            pass

    # Package manager
    if (root / "uv.lock").exists():
        profile.package_manager = "uv"
    elif (root / "poetry.lock").exists():
        profile.package_manager = "poetry"
    elif (root / "Pipfile").exists():
        profile.package_manager = "pipenv"
    else:
        profile.package_manager = "pip"

    # Collect all deps
    deps = _collect_python_deps(root)

    # Framework / project type
    for dep, template in FRAMEWORK_TO_TEMPLATE.items():
        if dep in deps:
            pt = template.replace("languages/", "")
            if pt not in profile.project_types and "project-types" in template:
                profile.project_types.append(template)
                result.add_template(template)
            profile.frameworks.append(dep)

    # Test runner
    if "pytest" in deps or (root / "pytest.ini").exists() or (root / "conftest.py").exists():
        profile.test_runner = "pytest"
    elif "unittest" in str(deps):
        profile.test_runner = "unittest"

    # Linter / formatter / type checker
    if "ruff" in deps:
        profile.linter = "ruff"
    elif "flake8" in deps:
        profile.linter = "flake8"
    elif "pylint" in deps:
        profile.linter = "pylint"

    if "black" in deps:
        profile.formatter = "black"
    elif "ruff" in deps and not profile.formatter:
        profile.formatter = "ruff format"

    if "mypy" in deps:
        profile.type_checker = "mypy"
    elif "pyright" in deps:
        profile.type_checker = "pyright"

    # Check if it's a library/SDK
    if (root / "pyproject.toml").exists():
        try:
            with open(root / "pyproject.toml", "rb") as f:
                data = tomllib.load(f)
            if data.get("project", {}).get("name") and not profile.project_types:
                profile.project_types.append("project-types/library-sdk.md")
                result.add_template("project-types/library-sdk.md", "inferred")
        except Exception:
            pass


def _collect_python_deps(root: Path) -> set[str]:
    deps: set[str] = set()

    def _norm(name: str) -> str:
        return name.lower().replace("-", "_")

    if (root / "pyproject.toml").exists():
        try:
            with open(root / "pyproject.toml", "rb") as f:
                data = tomllib.load(f)
            for dep in data.get("project", {}).get("dependencies", []):
                # "fastapi>=0.100" → "fastapi"
                pkg = re.split(r"[>=<!\[;\s]", dep)[0].strip()
                deps.add(_norm(pkg))
            for group in data.get("dependency-groups", {}).values():
                for dep in group:
                    if isinstance(dep, str):
                        pkg = re.split(r"[>=<!\[;\s]", dep)[0].strip()
                        deps.add(_norm(pkg))
            # tool.poetry.dependencies
            for dep in data.get("tool", {}).get("poetry", {}).get("dependencies", {}).keys():
                deps.add(_norm(dep))
        except Exception:
            pass

    if (root / "requirements.txt").exists():
        try:
            for line in (root / "requirements.txt").read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = re.split(r"[>=<!\[;\s]", line)[0].strip()
                    deps.add(_norm(pkg))
        except Exception:
            pass

    return deps


def _detect_javascript(root: Path, result: DetectionResult) -> None:
    pkg_file = root / "package.json"
    if not pkg_file.exists():
        return

    try:
        data = json.loads(pkg_file.read_text())
    except Exception:
        return

    profile = result.profile

    # Determine TypeScript vs JavaScript
    all_deps = {
        **data.get("dependencies", {}),
        **data.get("devDependencies", {}),
    }
    dep_names = {k.lower().lstrip("@").split("/")[-1] for k in all_deps}

    is_ts = (
        "typescript" in all_deps
        or list(root.glob("tsconfig*.json"))
        or list(root.glob("src/**/*.ts"))
    )

    lang = "typescript" if is_ts else "javascript"
    profile.languages.append(lang)
    result.add_template(LANGUAGE_TO_TEMPLATE[lang])

    if is_ts:
        result.add_template(LANGUAGE_TO_TEMPLATE["javascript"], "inferred")

    # Node version
    if (root / ".nvmrc").exists():
        profile.node_version = (root / ".nvmrc").read_text().strip().lstrip("v")
    elif (root / ".node-version").exists():
        profile.node_version = (root / ".node-version").read_text().strip().lstrip("v")

    # Package manager
    if (root / "pnpm-lock.yaml").exists():
        profile.package_manager = "pnpm"
    elif (root / "yarn.lock").exists():
        profile.package_manager = "yarn"
    elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        profile.package_manager = "bun"
    else:
        profile.package_manager = "npm"

    # Frameworks → project types
    for dep_key, template in FRAMEWORK_TO_TEMPLATE.items():
        norm_key = dep_key.lower().replace("-", "").replace("_", "")
        if any(norm_key in d.lower().replace("-", "").replace("_", "") for d in dep_names):
            if template not in profile.project_types and "project-types" in template:
                profile.project_types.append(template)
                result.add_template(template)
            if dep_key not in profile.frameworks:
                profile.frameworks.append(dep_key)

    # Test runner
    if "vitest" in dep_names:
        profile.test_runner = "vitest"
    elif "jest" in dep_names:
        profile.test_runner = "jest"
    elif "mocha" in dep_names:
        profile.test_runner = "mocha"

    # Linter / formatter
    if "eslint" in dep_names:
        profile.linter = "eslint"
    elif "biome" in dep_names:
        profile.linter = "biome"

    if "prettier" in dep_names:
        profile.formatter = "prettier"
    elif "biome" in dep_names and not profile.formatter:
        profile.formatter = "biome"

    # CSS detection
    if any(f.suffix == ".css" for f in root.rglob("*.css") if ".byakugan" not in str(f)):
        if "css" not in profile.languages:
            profile.languages.append("css")
            result.add_template(LANGUAGE_TO_TEMPLATE["css"], "inferred")


def _detect_rust(root: Path, result: DetectionResult) -> None:
    if not (root / "Cargo.toml").exists():
        return
    profile = result.profile
    profile.languages.append("rust")
    result.add_template(LANGUAGE_TO_TEMPLATE["rust"])
    profile.package_manager = "cargo"
    profile.test_runner = "cargo test"

    try:
        with open(root / "Cargo.toml", "rb") as f:
            data = tomllib.load(f)
        deps = set(data.get("dependencies", {}).keys())
        if "axum" in deps or "actix-web" in deps or "warp" in deps:
            profile.frameworks.extend([d for d in ["axum", "actix-web", "warp"] if d in deps])
            profile.project_types.append("project-types/web-backend.md")
            result.add_template("project-types/web-backend.md")
        if "clap" in deps or not (root / "src" / "lib.rs").exists():
            if not profile.project_types:
                profile.project_types.append("project-types/cli-tool.md")
                result.add_template("project-types/cli-tool.md", "inferred")
        if (root / "src" / "lib.rs").exists() and not profile.project_types:
            profile.project_types.append("project-types/library-sdk.md")
            result.add_template("project-types/library-sdk.md", "inferred")
    except Exception:
        pass


def _detect_go(root: Path, result: DetectionResult) -> None:
    if not (root / "go.mod").exists():
        return
    profile = result.profile
    profile.languages.append("go")
    result.add_template(LANGUAGE_TO_TEMPLATE["go"])
    profile.package_manager = "go mod"
    profile.test_runner = "go test"

    try:
        content = (root / "go.mod").read_text()
        if any(f in content for f in ["gin-gonic", "echo", "fiber", "chi", "gorilla/mux"]):
            profile.project_types.append("project-types/web-backend.md")
            result.add_template("project-types/web-backend.md")
    except Exception:
        pass


def _detect_java(root: Path, result: DetectionResult) -> None:
    has_gradle = (root / "build.gradle").exists() or (root / "build.gradle.kts").exists()
    has_maven = (root / "pom.xml").exists()
    if not has_gradle and not has_maven:
        return

    profile = result.profile
    profile.package_manager = "gradle" if has_gradle else "maven"

    # Kotlin vs Java
    has_kotlin = (
        (root / "build.gradle.kts").exists()
        or list(root.glob("**/*.kt"))
    )
    if has_kotlin:
        profile.languages.append("kotlin")
        result.add_template(LANGUAGE_TO_TEMPLATE["kotlin"])
    else:
        profile.languages.append("java")
        result.add_template(LANGUAGE_TO_TEMPLATE["java"])

    # Check for Spring Boot
    if has_maven:
        try:
            content = (root / "pom.xml").read_text()
            if "spring-boot" in content:
                profile.frameworks.append("spring-boot")
                profile.project_types.append("project-types/web-backend.md")
                result.add_template("project-types/web-backend.md")
        except Exception:
            pass

    # Check for Android
    if (root / "app").is_dir() and (root / "gradle.properties").exists():
        profile.project_types.append("project-types/mobile-app.md")
        result.add_template("project-types/mobile-app.md")


def _detect_ruby(root: Path, result: DetectionResult) -> None:
    if not (root / "Gemfile").exists():
        return
    profile = result.profile
    profile.languages.append("ruby")
    result.add_template(LANGUAGE_TO_TEMPLATE["ruby"])
    profile.package_manager = "bundler"

    try:
        content = (root / "Gemfile").read_text()
        if "rails" in content.lower():
            profile.frameworks.append("rails")
            profile.project_types.append("project-types/web-backend.md")
            result.add_template("project-types/web-backend.md")
        if "rspec" in content.lower():
            profile.test_runner = "rspec"
        if "rubocop" in content.lower():
            profile.linter = "rubocop"
            profile.formatter = "rubocop"
    except Exception:
        pass


def _detect_php(root: Path, result: DetectionResult) -> None:
    if not (root / "composer.json").exists():
        return
    profile = result.profile
    profile.languages.append("php")
    result.add_template(LANGUAGE_TO_TEMPLATE["php"])
    profile.package_manager = "composer"

    try:
        data = json.loads((root / "composer.json").read_text())
        deps = {**data.get("require", {}), **data.get("require-dev", {})}
        dep_keys = " ".join(deps.keys()).lower()
        if "laravel" in dep_keys:
            profile.frameworks.append("laravel")
            profile.project_types.append("project-types/web-backend.md")
            result.add_template("project-types/web-backend.md")
        elif "symfony" in dep_keys:
            profile.frameworks.append("symfony")
            profile.project_types.append("project-types/web-backend.md")
            result.add_template("project-types/web-backend.md")
        if "phpunit" in dep_keys:
            profile.test_runner = "phpunit"
        if "phpstan" in dep_keys:
            profile.linter = "phpstan"
    except Exception:
        pass


def _detect_swift(root: Path, result: DetectionResult) -> None:
    has_package = (root / "Package.swift").exists()
    has_xcodeproj = list(root.glob("*.xcodeproj")) or list(root.glob("*.xcworkspace"))
    if not has_package and not has_xcodeproj:
        return

    profile = result.profile
    profile.languages.append("swift")
    result.add_template(LANGUAGE_TO_TEMPLATE["swift"])
    profile.package_manager = "swift pm" if has_package else "xcode"
    profile.test_runner = "xcodebuild test"

    if has_xcodeproj:
        profile.project_types.append("project-types/mobile-app.md")
        result.add_template("project-types/mobile-app.md")


def _detect_c_cpp(root: Path, result: DetectionResult) -> None:
    has_cpp = list(root.glob("**/*.cpp")) or list(root.glob("**/*.cc")) or list(root.glob("**/*.cxx"))
    has_c = list(root.glob("**/*.c")) and not has_cpp
    has_cmake = (root / "CMakeLists.txt").exists()

    profile = result.profile

    if has_cpp:
        profile.languages.append("cpp")
        result.add_template(LANGUAGE_TO_TEMPLATE["cpp"])
        profile.package_manager = "cmake" if has_cmake else None
    elif has_c:
        profile.languages.append("c")
        result.add_template(LANGUAGE_TO_TEMPLATE["c"])
        profile.package_manager = "make" if (root / "Makefile").exists() else None


def _infer_project_type(root: Path, result: DetectionResult) -> None:
    profile = result.profile
    if profile.project_types:
        return  # already detected

    # Infrastructure indicators
    has_docker = (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists()
    has_tf = list(root.glob("*.tf")) or list(root.glob("**/*.tf"))
    has_k8s = list(root.glob("**/*.yaml")) and (root / ".github" / "workflows").is_dir()

    if has_tf or (has_docker and has_k8s):
        profile.project_types.append("project-types/devops-infrastructure.md")
        result.add_template("project-types/devops-infrastructure.md", "inferred")

    # CLI indicators
    if not profile.project_types:
        if any(f.name in ("Makefile", "Taskfile.yml") for f in root.iterdir() if f.is_file()):
            profile.project_types.append("project-types/cli-tool.md")
            result.add_template("project-types/cli-tool.md", "inferred")
