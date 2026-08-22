from __future__ import annotations

import httpx

from app.config import settings

LANG_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "od": "od-IN",
}


class Sarvam:
    def __init__(self) -> None:
        self.key = settings.sarvam_api_key
        self.base = settings.sarvam_base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.key)

    def _headers(self) -> dict[str, str]:
        return {"api-subscription-key": self.key}

    async def translate(self, text: str, source: str, target: str) -> str:
        if not self.enabled or source == target:
            return text
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base}/translate",
                headers=self._headers(),
                json={
                    "input": text,
                    "source_language_code": LANG_MAP.get(source, source),
                    "target_language_code": LANG_MAP.get(target, target),
                    "speaker_gender": "Male",
                    "mode": "formal",
                    "model": "mayura:v1",
                    "enable_preprocessing": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("translated_text") or data.get("output") or text

    async def chat(self, system: str, user: str) -> str | None:
        if not self.enabled:
            return None
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base}/v1/chat/completions",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={
                    "model": "sarvam-m",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                },
            )
            if resp.status_code >= 400:
                return None
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        if not self.enabled:
            return ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base}/speech-to-text",
                headers=self._headers(),
                files={"file": (filename, audio, content_type or "audio/wav")},
                data={"model": "saaras:v3", "mode": "transcribe"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("transcript") or data.get("text") or ""

    async def tts(self, text: str, lang: str) -> bytes | None:
        if not self.enabled:
            return None
        speaker = "anushka"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base}/text-to-speech",
                headers=self._headers(),
                json={
                    "inputs": [text[:2400]],
                    "target_language_code": LANG_MAP.get(lang, "en-IN"),
                    "speaker": speaker,
                    "model": "bulbul:v2",
                },
            )
            if resp.status_code >= 400:
                return None
            data = resp.json()
            audio_b64 = (data.get("audios") or [None])[0]
            if not audio_b64:
                return None
            import base64

            return base64.b64decode(audio_b64)


sarvam = Sarvam()
