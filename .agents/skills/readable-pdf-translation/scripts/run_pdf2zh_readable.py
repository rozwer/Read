#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


PATCH_VERSION = 2


FONT_LINE = "            size: float = pstk[id].size                 # 段落字体大小"
FONT_PATCH = """            size: float = pstk[id].size                 # 段落字体大小
            is_japanese_prose = self.translator.lang_out.lower() == \"ja\" and pstk[id].brk and re.search(r\"[ぁ-んァ-ヶ一-龯]\", new)
            if is_japanese_prose:
                size *= float(os.getenv(\"READABLE_PDF_FONT_SCALE\", \"0.92\"))  # CODEX_READABLE_FONT_SCALE
                width_scale = float(os.getenv(\"READABLE_PDF_WIDTH_SCALE\", \"1.04\"))
                width_expansion = (x1 - x0) * (width_scale - 1.0) / 2.0
                x0 = max(0.0, x0 - width_expansion)
                x1 = min(ltpage.width, x1 + width_expansion)  # CODEX_READABLE_WIDTH_SCALE"""
IMPORT_LINE = "import logging\n"
IMPORT_PATCH = "import logging\nimport os\n"
ADV_LINE = "                x += adv\n                if log.isEnabledFor(logging.DEBUG):"
ADV_PATCH = """                x += adv
                if brk and not vy_regex and ptr < len(new) and os.getenv("READABLE_PDF_PUNCTUATION_AWARE", "1") == "1":
                    width_used = x - x0
                    available_width = max(x1 - x0, 1.0)
                    sentence_threshold = float(os.getenv(\"READABLE_PDF_SENTENCE_BREAK\", \"0.58\"))
                    comma_threshold = float(os.getenv(\"READABLE_PDF_COMMA_BREAK\", \"0.82\"))
                    punctuation_break = (
                        ch in \"。！？!?\" and width_used >= available_width * sentence_threshold
                    ) or (
                        ch in \"、；：;:\" and width_used >= available_width * comma_threshold
                    )
                    if punctuation_break:  # CODEX_READABLE_PUNCTUATION_BREAK
                        if cstk:
                            ops_vals.append({
                                \"type\": OpType.TEXT,
                                \"font\": fcur,
                                \"size\": size,
                                \"x\": tx,
                                \"dy\": 0,
                                \"rtxt\": raw_string(fcur, cstk),
                                \"lidx\": lidx,
                            })
                            cstk = \"\"
                        x = x0
                        lidx += 1
                if log.isEnabledFor(logging.DEBUG):"""
CHAR_LINE = """                    ptr += 1
                if (                                # 输出文字缓冲区"""
CHAR_PATCH = """                    ptr += 1
                no_break_before = not vy_regex and ch in \"、。，．！？!?；：;:）］｝〉》」』】〕…\"
                if (                                # 输出文字缓冲区"""
WIDTH_LINE = "                    or x + adv > x1 + 0.1 * size    # 3. 到达右边界（可能一整行都被符号化，这里需要考虑浮点误差）"
WIDTH_PATCH = "                    or (x + adv > x1 + 0.1 * size and not no_break_before)  # 3. 到达右边界；句読点はぶら下げる"
WRAP_LINE = "                if brk and x + adv > x1 + 0.1 * size:  # 到达右边界且原文段落存在换行"
WRAP_PATCH = "                if brk and x + adv > x1 + 0.1 * size and not no_break_before:  # 到达右边界且原文段落存在换行"


def find_interpreter(explicit: Path | None = None) -> Path:
    if explicit is not None:
        if not explicit.is_file():
            raise SystemExit(f"pdf2zh Python not found: {explicit}")
        return explicit.absolute()

    # Both setup scripts install pdf2zh in uv's isolated tool environment.
    # Windows console launchers are binary .exe files, not shebang scripts.
    uv = shutil.which("uv")
    if uv:
        result = subprocess.run(
            [uv, "tool", "dir"], capture_output=True, text=True,
            encoding="utf-8", check=True,
        )
        tool_dir = Path(result.stdout.strip()) / "pdf2zh"
        candidate = tool_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if candidate.is_file():
            return candidate.absolute()

    executable_name = shutil.which("pdf2zh")
    if executable_name:
        executable = Path(executable_name).resolve()
        if executable.suffix.lower() == ".exe":
            candidate = executable.with_name("python.exe")
            if candidate.is_file():
                return candidate
        else:
            with executable.open("rb") as stream:
                first = stream.readline().decode("utf-8").strip()
            if first.startswith("#!"):
                candidate = Path(first[2:].strip().strip('"'))
                if candidate.is_file():
                    return candidate
    raise SystemExit(
        "pdf2zh Python not found. Run the repository setup script, or pass "
        "--pdf2zh-python /absolute/path/to/the/python-containing-pdf2zh"
    )


def interpreter_and_package(interpreter: Path) -> tuple[Path, Path]:
    result = subprocess.run(
        [
            str(interpreter),
            "-I",
            "-X", "utf8",
            "-c",
            "import importlib.util; "
            "spec = importlib.util.find_spec('pdf2zh'); "
            "assert spec and spec.submodule_search_locations, 'pdf2zh is not installed'; "
            "print(spec.submodule_search_locations[0])",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    package = Path(result.stdout.strip().splitlines()[-1])
    if not (package / "converter.py").is_file():
        raise SystemExit(f"pdf2zh converter not found: {package}")
    return interpreter, package


def prepare_runtime(runtime_dir: Path, source_package: Path) -> Path:
    runtime_dir = runtime_dir.resolve()
    if runtime_dir == Path(runtime_dir.anchor):
        raise SystemExit("runtime directory must not be a filesystem root")
    package = runtime_dir / "pdf2zh"
    source_hash = hashlib.sha256((source_package / "converter.py").read_bytes()).hexdigest()
    metadata_path = runtime_dir / "readable-runtime.json"
    if package.exists():
        if not metadata_path.exists():
            raise SystemExit(f"existing runtime is not managed by this script: {runtime_dir}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("source_converter_sha256") != source_hash:
            raise SystemExit("installed pdf2zh changed; choose a new --runtime-dir")
        if metadata.get("patch_version") != PATCH_VERSION:
            raise SystemExit("readable patch changed; choose a new --runtime-dir")
        return runtime_dir

    runtime_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_package, package)
    converter = package / "converter.py"
    text = converter.read_text(encoding="utf-8")
    for old, new, label in (
        (IMPORT_LINE, IMPORT_PATCH, "os import"),
        (FONT_LINE, FONT_PATCH, "font scale"),
        (CHAR_LINE, CHAR_PATCH, "Japanese line-start prohibition"),
        (WIDTH_LINE, WIDTH_PATCH, "hanging punctuation width"),
        (WRAP_LINE, WRAP_PATCH, "hanging punctuation wrap"),
        (ADV_LINE, ADV_PATCH, "punctuation break"),
    ):
        if text.count(old) != 1:
            raise SystemExit(f"cannot patch pdf2zh {label}; expected source pattern not found once")
        text = text.replace(old, new)
    converter.write_text(text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "source_package": str(source_package),
                "source_converter_sha256": source_hash,
                "patch_version": PATCH_VERSION,
                "patch": "Japanese prose font/width scale, punctuation-aware breaks, and kinsoku",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument(
        "--pdf2zh-python", type=Path,
        help="Python in the pdf2zh environment; defaults to the uv tool installation",
    )
    parser.add_argument(
        "--preset",
        choices=("readable", "standard"),
        default="readable",
        help="readable: compact Japanese with punctuation-aware breaks; standard: source-size Japanese with ordinary wrapping",
    )
    parser.add_argument("--font-scale", type=float)
    parser.add_argument("--width-scale", type=float)
    parser.add_argument("--sentence-threshold", type=float)
    parser.add_argument("--comma-threshold", type=float)
    parser.add_argument("pdf2zh_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    preset = {
        "readable": {
            "font_scale": 0.92,
            "width_scale": 1.04,
            "sentence_threshold": 0.58,
            "comma_threshold": 0.82,
            "punctuation_aware": True,
        },
        "standard": {
            "font_scale": 1.0,
            "width_scale": 1.0,
            "sentence_threshold": 1.0,
            "comma_threshold": 1.0,
            "punctuation_aware": False,
        },
    }[args.preset]
    for key in ("font_scale", "width_scale", "sentence_threshold", "comma_threshold"):
        if getattr(args, key) is None:
            setattr(args, key, preset[key])
    if not 0.75 <= args.font_scale <= 1.0:
        raise SystemExit("font scale must be between 0.75 and 1.0")
    if not 1.0 <= args.width_scale <= 1.08:
        raise SystemExit("width scale must be between 1.0 and 1.08")
    if not 0.3 <= args.sentence_threshold <= 1.0:
        raise SystemExit("sentence threshold must be between 0.3 and 1.0")
    if not 0.5 <= args.comma_threshold <= 1.0:
        raise SystemExit("comma threshold must be between 0.5 and 1.0")
    if not args.pdf2zh_args:
        raise SystemExit("pass pdf2zh arguments after --")
    forwarded = args.pdf2zh_args[1:] if args.pdf2zh_args[0] == "--" else args.pdf2zh_args

    interpreter, source_package = interpreter_and_package(find_interpreter(args.pdf2zh_python))
    runtime = prepare_runtime(args.runtime_dir, source_package)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(runtime) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["READABLE_PDF_FONT_SCALE"] = str(args.font_scale)
    env["READABLE_PDF_WIDTH_SCALE"] = str(args.width_scale)
    env["READABLE_PDF_SENTENCE_BREAK"] = str(args.sentence_threshold)
    env["READABLE_PDF_COMMA_BREAK"] = str(args.comma_threshold)
    env["READABLE_PDF_PUNCTUATION_AWARE"] = "1" if preset["punctuation_aware"] else "0"
    command = [str(interpreter), "-m", "pdf2zh.pdf2zh", *forwarded]
    raise SystemExit(subprocess.run(command, env=env).returncode)


if __name__ == "__main__":
    main()
