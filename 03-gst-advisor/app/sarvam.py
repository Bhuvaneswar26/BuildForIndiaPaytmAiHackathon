from __future__ import annotations

import asyncio

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
        self.base = settings.sarvam_base_url.rstrip("/")

    @property
    def key(self) -> str:
        return settings.sarvam_key

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
                    "max_tokens": 1800,
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
        language_code = LANG_MAP.get(lang, "en-IN")
        try:
            from sarvamai import SarvamAI

            client = SarvamAI(api_subscription_key=self.key)
            audio_chunks = await asyncio.to_thread(
                client.text_to_speech.convert_stream,
                text=text[:2400],
                language_code=language_code,
                speaker=settings.sarvam_tts_speaker,
                model=settings.sarvam_tts_model,
                pace=settings.sarvam_tts_pace,
                speech_sample_rate=settings.sarvam_tts_sample_rate,
                output_audio_codec="wav",
            )
            return b"".join(audio_chunks)
        except (ImportError, AttributeError, TypeError):
            pass

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base}/text-to-speech",
                headers=self._headers(),
                json={
                    "inputs": [text[:2400]],
                    "target_language_code": language_code,
                    "speaker": settings.sarvam_tts_speaker,
                    "model": settings.sarvam_tts_model,
                    "pace": settings.sarvam_tts_pace,
                    "speech_sample_rate": settings.sarvam_tts_sample_rate,
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
