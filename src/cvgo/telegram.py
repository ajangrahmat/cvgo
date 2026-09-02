"""Notifikasi teks dan gambar melalui Telegram Bot API."""

from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


class Telegram:
    """Kirim pesan dan frame kamera ke sebuah chat Telegram."""

    API_ROOT = "https://api.telegram.org"

    def __init__(
        self,
        token: str | None = None,
        chat_id: str | int | None = None,
        *,
        cooldown: float = 30.0,
        timeout: float = 15.0,
        silent: bool = False,
        protect: bool = False,
    ) -> None:
        token = token or os.environ.get("CVGO_TELEGRAM_TOKEN")
        chat_id = chat_id or os.environ.get("CVGO_TELEGRAM_CHAT_ID")

        if not token:
            raise ValueError(
                "Isi token atau environment variable CVGO_TELEGRAM_TOKEN"
            )
        if cooldown < 0:
            raise ValueError("cooldown tidak boleh negatif")
        if timeout <= 0:
            raise ValueError("timeout harus lebih dari 0")

        self.token = token
        self.chat_id = str(chat_id) if chat_id is not None else None
        self.cooldown = float(cooldown)
        self.timeout = float(timeout)
        self.silent = silent
        self.protect = protect
        self.last_response: Any | None = None
        self.last_error: str | None = None
        self._sent_at: dict[str, float] = {}

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def ready(
        self,
        key: str = "default",
        *,
        now: float | None = None,
    ) -> bool:
        """Periksa apakah cooldown untuk sebuah jenis notifikasi selesai."""
        if self.cooldown == 0:
            return True

        last_sent = self._sent_at.get(key)
        if last_sent is None:
            return True

        now = time.monotonic() if now is None else now
        return now - last_sent >= self.cooldown

    def remaining(
        self,
        key: str = "default",
        *,
        now: float | None = None,
    ) -> float:
        """Kembalikan sisa cooldown dalam detik."""
        last_sent = self._sent_at.get(key)
        if last_sent is None:
            return 0.0

        now = time.monotonic() if now is None else now
        return max(0.0, self.cooldown - (now - last_sent))

    def reset(self, key: str | None = None) -> None:
        """Reset satu cooldown atau seluruh cooldown notifikasi."""
        if key is None:
            self._sent_at.clear()
        else:
            self._sent_at.pop(key, None)

    def find_chat_id(self) -> str | None:
        """Ambil chat ID terbaru setelah pengguna mengirim pesan ke bot."""
        updates = self._request(
            "getUpdates",
            urllib.parse.urlencode({"timeout": 0}).encode(),
            "application/x-www-form-urlencoded",
        )
        if updates is None:
            return None

        message_types = (
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "business_message",
        )
        for update in reversed(updates):
            for message_type in message_types:
                message = update.get(message_type)
                chat = message.get("chat") if message else None
                if chat and "id" in chat:
                    self.chat_id = str(chat["id"])
                    return self.chat_id

        self.last_error = "Chat belum ditemukan. Kirim /start ke bot terlebih dulu."
        return None

    def send_message(
        self,
        text: str,
        *,
        key: str = "message",
        force: bool = False,
        silent: bool | None = None,
        protect: bool | None = None,
        parse_mode: str | None = None,
    ) -> bool:
        """Kirim satu pesan teks."""
        if not 1 <= len(text) <= 4096:
            raise ValueError("Panjang pesan harus antara 1 dan 4096 karakter")
        if not self._allowed(key, force):
            return False

        fields = self._message_fields(
            silent=silent,
            protect=protect,
        )
        fields["text"] = text
        if parse_mode:
            fields["parse_mode"] = parse_mode

        data = urllib.parse.urlencode(fields).encode()
        result = self._request(
            "sendMessage",
            data,
            "application/x-www-form-urlencoded",
        )
        if result is None:
            return False

        self._mark_sent(key)
        return True

    def send_photo(
        self,
        photo,
        caption: str = "",
        *,
        key: str = "photo",
        force: bool = False,
        filename: str | None = None,
        quality: int = 85,
        silent: bool | None = None,
        protect: bool | None = None,
        parse_mode: str | None = None,
    ) -> bool:
        """Kirim frame OpenCV, bytes gambar, atau file gambar."""
        if len(caption) > 1024:
            raise ValueError("Caption maksimal 1024 karakter")
        if not 1 <= quality <= 100:
            raise ValueError("quality harus antara 1 dan 100")
        if not self._allowed(key, force):
            return False

        data, filename, content_type = self._photo_data(
            photo,
            filename=filename,
            quality=quality,
        )
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Ukuran foto maksimal 10 MB")

        fields = self._message_fields(
            silent=silent,
            protect=protect,
        )
        if caption:
            fields["caption"] = caption
        if parse_mode:
            fields["parse_mode"] = parse_mode

        body, boundary = self._multipart(
            fields,
            data=data,
            filename=filename,
            content_type=content_type,
        )
        result = self._request(
            "sendPhoto",
            body,
            f"multipart/form-data; boundary={boundary}",
        )
        if result is None:
            return False

        self._mark_sent(key)
        return True

    def _message_fields(
        self,
        *,
        silent: bool | None,
        protect: bool | None,
    ) -> dict[str, str]:
        if self.chat_id is None:
            raise RuntimeError(
                "chat_id belum diisi. Isi CVGO_TELEGRAM_CHAT_ID "
                "atau jalankan find_chat_id()."
            )

        use_silent = self.silent if silent is None else silent
        use_protect = self.protect if protect is None else protect
        return {
            "chat_id": self.chat_id,
            "disable_notification": str(use_silent).lower(),
            "protect_content": str(use_protect).lower(),
        }

    def _allowed(self, key: str, force: bool) -> bool:
        if force or self.ready(key):
            self.last_error = None
            return True

        remaining = self.remaining(key)
        self.last_error = f"Cooldown {key!r} masih aktif {remaining:.1f} detik."
        return False

    def _mark_sent(self, key: str) -> None:
        self._sent_at[key] = time.monotonic()

    @staticmethod
    def _photo_data(
        photo,
        *,
        filename: str | None,
        quality: int,
    ) -> tuple[bytes, str, str]:
        if isinstance(photo, (str, os.PathLike)):
            path = Path(photo).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"Foto tidak ditemukan: {path}")
            data = path.read_bytes()
            filename = filename or path.name
            content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        elif isinstance(photo, (bytes, bytearray, memoryview)):
            data = bytes(photo)
            filename = filename or "cvgo.jpg"
            content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        else:
            try:
                import cv2
            except ImportError as exc:
                raise ImportError("OpenCV belum terpasang.") from exc

            ok, encoded = cv2.imencode(
                ".jpg",
                photo,
                [cv2.IMWRITE_JPEG_QUALITY, quality],
            )
            if not ok:
                raise ValueError("Frame tidak dapat diubah menjadi JPEG")
            data = encoded.tobytes()
            filename = filename or "cvgo.jpg"
            content_type = "image/jpeg"

        filename = Path(filename).name
        filename = filename.replace('"', "_")
        filename = filename.replace("\r", "").replace("\n", "")
        if not filename:
            filename = "cvgo.jpg"
        return data, filename, content_type

    @staticmethod
    def _multipart(
        fields: dict[str, str],
        *,
        data: bytes,
        filename: str,
        content_type: str,
    ) -> tuple[bytes, str]:
        boundary = f"cvgo-{uuid.uuid4().hex}"
        body = bytearray()

        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            )
            body.extend(value.encode("utf-8"))
            body.extend(b"\r\n")

        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                'Content-Disposition: form-data; name="photo"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(data)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode())
        return bytes(body), boundary

    def _request(
        self,
        method: str,
        data: bytes,
        content_type: str,
    ):
        self.last_error = None
        self.last_response = None
        request = urllib.request.Request(
            f"{self.API_ROOT}/bot{self.token}/{method}",
            data=data,
            headers={
                "Content-Type": content_type,
                "User-Agent": "CVGO/0.1",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            self.last_error = self._http_error(exc)
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", str(exc))
            self.last_error = f"Telegram tidak dapat dihubungi: {reason}"
            return None
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.last_error = "Respons Telegram tidak valid."
            return None

        if not isinstance(payload, dict):
            self.last_error = "Respons Telegram tidak valid."
            return None
        if not payload.get("ok"):
            self.last_error = payload.get("description", "Permintaan Telegram gagal.")
            return None

        self.last_response = payload.get("result")
        return self.last_response

    @staticmethod
    def _http_error(error: urllib.error.HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            if not isinstance(payload, dict):
                return f"Telegram HTTP {error.code}"
            return payload.get("description", f"Telegram HTTP {error.code}")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return f"Telegram HTTP {error.code}"
