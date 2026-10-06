import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pymupdf
import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / '.agents/skills/readable-pdf-translation/scripts'
spec = importlib.util.spec_from_file_location('readable_runtime', SCRIPTS / 'run_pdf2zh_readable.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def test_explicit_interpreter_does_not_require_launcher(monkeypatch):
    monkeypatch.setattr(runtime.shutil, 'which', lambda _: None)
    assert runtime.find_interpreter(Path(sys.executable)) == Path(sys.executable).absolute()
    with pytest.raises(SystemExit, match='Python not found'):
        runtime.find_interpreter(Path('missing-python.exe'))


def test_uv_windows_environment_with_spaces_and_unicode(tmp_path, monkeypatch):
    tools = tmp_path / 'tools 日本語 with spaces'
    python = tools / 'pdf2zh/Scripts/python.exe'
    python.parent.mkdir(parents=True)
    python.write_bytes(b'MZ\x00\xff')
    monkeypatch.setattr(runtime, 'os', SimpleNamespace(name='nt'))
    monkeypatch.setattr(runtime.shutil, 'which', lambda name: 'uv.exe' if name == 'uv' else None)

    def uv_dir(command, **kwargs):
        assert command == ['uv.exe', 'tool', 'dir']
        return subprocess.CompletedProcess(command, 0, stdout=str(tools) + '\n')

    monkeypatch.setattr(runtime.subprocess, 'run', uv_dir)
    assert runtime.find_interpreter() == python.absolute()


def test_binary_launcher_is_not_decoded_as_text(tmp_path, monkeypatch):
    launcher = tmp_path / 'pdf2zh.exe'
    launcher.write_bytes(b'MZ\x00\xff')
    python = tmp_path / 'python.exe'
    python.write_bytes(b'MZ\x00\xff')
    monkeypatch.setattr(runtime.shutil, 'which', lambda name: str(launcher) if name == 'pdf2zh' else None)
    assert runtime.find_interpreter() == python
    python.unlink()
    with pytest.raises(SystemExit, match='--pdf2zh-python'):
        runtime.find_interpreter()


def test_script_launcher_path_with_spaces(tmp_path, monkeypatch):
    python = tmp_path / 'Python folder' / 'python'
    python.parent.mkdir()
    python.write_bytes(b'')
    launcher = tmp_path / 'pdf2zh'
    launcher.write_text(f'#!{python}\n', encoding='utf-8')
    monkeypatch.setattr(runtime.shutil, 'which', lambda name: str(launcher) if name == 'pdf2zh' else None)
    assert runtime.find_interpreter() == python


def run_script(script, *args, check=True):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *(str(arg) for arg in args)],
        capture_output=True, text=True, encoding='utf-8', check=check,
        env={**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'},
    )


def make_pdf(path, text):
    with pymupdf.open() as doc:
        for _ in range(2):
            page = doc.new_page(width=300, height=400)
            page.insert_text((30, 50), text, fontname='japan', fontsize=12)
        doc.save(path)


def test_pdf_composition_and_rendering_with_unicode_paths(tmp_path):
    folder = tmp_path / '日本語 with spaces'
    folder.mkdir()
    source, translated, final = (folder / name for name in ('原文.pdf', '訳文.pdf', '対訳.pdf'))
    make_pdf(source, 'Source paper')
    make_pdf(translated, '翻訳の検証')
    run_script('side_by_side_readable.py', translated, source, final)
    with pymupdf.open(final) as doc:
        assert len(doc) == 2
        page = doc[0]
        assert page.rect.width == 612
        assert page.rect.height == 400
        assert page.search_for('翻訳の検証')[0].x0 < 300
        assert page.search_for('Source paper')[0].x0 > 312
    images = folder / '画像'
    result = run_script('inspect_pdf.py', final, '--render-dir', images, '--pages', '2', '--dpi', 72)
    metadata = json.loads(result.stdout)
    assert metadata['pages'] == 2
    assert metadata['selected'][0]['page'] == 2
    image = pymupdf.Pixmap(str(images / 'page-0002.png'))
    assert (image.width, image.height) == (612, 400)
    assert not (images / 'page-0001.png').exists()
    result = run_script('inspect_pdf.py', final, '--pages', '3', check=False)
    assert result.returncode != 0
    assert '--pages must be in 1..2' in result.stderr


def test_all_skill_clis_load():
    for script in SCRIPTS.glob('*.py'):
        run_script(script.name, '--help')
