"""Validasi parameter publik CVGO dengan pesan error yang konsisten."""

from __future__ import annotations

from numbers import Integral, Real
from typing import TypeVar


T = TypeVar("T")


def boolean(name: str, value) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} harus bool")
    return value


def positive_int(name: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} harus bilangan bulat")
    if value <= 0:
        raise ValueError(f"{name} harus lebih dari 0")
    return int(value)


def non_negative_int(name: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} harus bilangan bulat")
    if value < 0:
        raise ValueError(f"{name} tidak boleh negatif")
    return int(value)


def positive_number(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} harus berupa angka")
    if value <= 0:
        raise ValueError(f"{name} harus lebih dari 0")
    return float(value)


def non_negative_number(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} harus berupa angka")
    if value < 0:
        raise ValueError(f"{name} tidak boleh negatif")
    return float(value)


def confidence(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} harus berupa angka")
    if not 0 <= value <= 1:
        raise ValueError(f"{name} harus antara 0 dan 1")
    return float(value)


def choice(name: str, value: T, choices: tuple[T, ...]) -> T:
    if isinstance(value, bool) and any(type(item) is int for item in choices):
        raise TypeError(f"{name} harus bilangan bulat")
    if value not in choices:
        options = ", ".join(map(str, choices))
        raise ValueError(f"{name} harus salah satu dari: {options}")
    return value
