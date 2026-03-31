from pathlib import Path

import run


def test_build_browser_launch_command_uses_app_mode(tmp_path):
    browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = tmp_path / "browser-profile"
    url = "http://127.0.0.1:5000/auth/login"

    command = run.build_browser_launch_command(browser_path, url, profile_dir)

    assert command[0] == browser_path
    assert "--new-window" in command
    assert f"--app={url}" in command
    assert f"--user-data-dir={profile_dir}" in command
    assert "--no-first-run" in command
    assert "--disable-extensions" in command
    assert "--disable-sync" in command
    assert "--guest" in command


def test_build_browser_launch_command_adds_edge_privacy_flags(tmp_path):
    browser_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    profile_dir = tmp_path / "browser-profile"
    url = "http://127.0.0.1:5000/auth/login"

    command = run.build_browser_launch_command(browser_path, url, profile_dir)

    assert "--inprivate" in command
    assert "--disable-features=msImplicitSignin,EdgeIdentitySyncPromo" in command


def test_browser_runtime_metadata_roundtrip_and_cleanup(tmp_path):
    runtime_file = tmp_path / "browser_runtime.json"
    profile_dir = tmp_path / "browser-profile"
    profile_dir.mkdir()
    marker = profile_dir / "marker.txt"
    marker.write_text("ok", encoding="utf-8")

    payload = run.write_browser_runtime(
        runtime_file,
        browser_path="msedge.exe",
        pid=4321,
        profile_dir=profile_dir,
        url="http://127.0.0.1:5000/auth/login",
    )

    restored = run.read_browser_runtime(runtime_file)

    assert payload == restored
    assert restored["pid"] == 4321
    assert restored["profile_dir"] == str(profile_dir)

    run.cleanup_browser_runtime(runtime_file)

    assert not runtime_file.exists()
    assert not profile_dir.exists()


def test_should_launch_browser_respects_environment(monkeypatch):
    monkeypatch.delenv("SFP_NO_BROWSER", raising=False)
    monkeypatch.delenv("SFP_VALIDATE_ONLY", raising=False)
    monkeypatch.delenv("CI", raising=False)
    assert run.should_launch_browser() is True

    monkeypatch.setenv("SFP_NO_BROWSER", "1")
    assert run.should_launch_browser() is False

    monkeypatch.delenv("SFP_NO_BROWSER", raising=False)
    monkeypatch.setenv("SFP_VALIDATE_ONLY", "1")
    assert run.should_launch_browser() is False

    monkeypatch.delenv("SFP_VALIDATE_ONLY", raising=False)
    monkeypatch.setenv("CI", "true")
    assert run.should_launch_browser() is False
