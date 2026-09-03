"""Command-line diagnostics untuk ``python -m cvgo``."""

from __future__ import annotations

import argparse
import json

from .diagnostics import check_camera, checks_passed, system_info


def _source(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m cvgo",
        description="Periksa instalasi dan perangkat CVGO.",
    )
    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check", help="periksa versi dependency")
    check.add_argument(
        "--camera",
        type=_source,
        help="uji source kamera, misalnya 0, 4, atau URL",
    )
    check.add_argument(
        "--backend",
        type=int,
        help="backend OpenCV; default CAP_ANY",
    )
    check.add_argument("--json", action="store_true", help="format JSON")
    return parser


def _print_text(info) -> None:
    python_mark = "OK" if info["python_supported"] else "ERROR"
    print(f"CVGO {info['cvgo']} diagnostics")
    print(
        f"Python {info['python']} ({info['implementation']}) "
        f"[{python_mark}]"
    )
    print(
        f"System {info['system']} {info['release']} / "
        f"{info['machine'] or 'unknown'}"
    )

    for item in info["dependencies"].values():
        installed = item["version"] or "not installed"
        mark = "OK" if item["ok"] else "ERROR"
        print(
            f"{item['name']}: {installed} "
            f"(expected {item['expected']}) [{mark}]"
        )

    camera = info.get("camera")
    if camera:
        if camera["ok"]:
            print(
                f"Camera {camera['source']}: "
                f"{camera['width']}x{camera['height']} [OK]"
            )
        else:
            print(f"Camera {camera['source']}: {camera['error']} [ERROR]")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    info = system_info()
    if args.camera is not None:
        info["camera"] = check_camera(args.camera, backend=args.backend)

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        _print_text(info)

    ok = checks_passed(info)
    if "camera" in info:
        ok = ok and info["camera"]["ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
