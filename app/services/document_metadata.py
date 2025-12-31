from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadataResult:
    doc_type: str
    extracted_name: Optional[str]
    extracted_metadata: dict[str, Any]


class DocumentMetadataService:
    def __init__(self) -> None:
        self._anthropic_api_key = settings.anthropic_api_key

    async def classify_and_extract(
        self,
        *,
        text: str,
        filename: str | None = None,
    ) -> DocumentMetadataResult:
        if self._anthropic_api_key:
            try:
                return await self._classify_and_extract_claude(text=text, filename=filename)
            except Exception as e:
                logger.warning("Claude metadata extraction failed, falling back. err=%s", e)

        return self._classify_and_extract_fallback(text=text, filename=filename)

    async def _classify_and_extract_claude(
        self,
        *,
        text: str,
        filename: str | None = None,
    ) -> DocumentMetadataResult:
        # Anthropic Messages API
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self._anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        truncated_text = text[:12000]
        prompt = (
            "You are a document classifier and metadata extractor.\n"
            "Return ONLY valid JSON with the following keys:\n"
            "doc_type: one of [cv, report, article, other]\n"
            "extracted_name: string|null (for CVs: candidate name; else best title)\n"
            "extracted_metadata: object with relevant metadata.\n\n"
            "For CV: include keys like name, email, phone, skills(list), experience(list), education(list).\n"
            "For general docs: include title, author, topics(list), summary.\n\n"
            f"filename: {filename or ''}\n\n"
            "DOCUMENT TEXT (truncated):\n"
            f"{truncated_text}"
        )

        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 800,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Expect a single text block containing JSON
        content = data.get("content", [])
        text_blocks = [c.get("text", "") for c in content if c.get("type") == "text"]
        raw = "\n".join(text_blocks).strip()

        try:
            parsed = json.loads(raw)
        except Exception:
            # Some models wrap JSON in fences; try to extract first JSON object.
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))

        doc_type = str(parsed.get("doc_type") or "other").lower()
        if doc_type not in {"cv", "report", "article", "other"}:
            doc_type = "other"

        extracted_name = parsed.get("extracted_name")
        if extracted_name is not None:
            extracted_name = str(extracted_name).strip() or None

        extracted_metadata = parsed.get("extracted_metadata")
        if not isinstance(extracted_metadata, dict):
            extracted_metadata = {}

        return DocumentMetadataResult(
            doc_type=doc_type,
            extracted_name=extracted_name,
            extracted_metadata=extracted_metadata,
        )

    def _classify_and_extract_fallback(
        self,
        *,
        text: str,
        filename: str | None = None,
    ) -> DocumentMetadataResult:
        lowered = text.lower()
        doc_type = "other"

        cv_signals = [
            "curriculum vitae",
            "resume",
            "work experience",
            "professional experience",
            "education",
            "skills",
        ]
        if any(s in lowered for s in cv_signals):
            doc_type = "cv"
        elif "abstract" in lowered or "references" in lowered:
            doc_type = "article"
        elif "executive summary" in lowered or "table of contents" in lowered:
            doc_type = "report"

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        top_lines = lines[:15]

        # naive name guess for CV: first non-empty line with letters and spaces only
        extracted_name: Optional[str] = None
        if doc_type == "cv":
            for ln in top_lines:
                if len(ln) <= 60 and re.fullmatch(r"[A-Za-z .'-]+", ln):
                    extracted_name = ln.strip()
                    break

        if extracted_name is None and filename:
            extracted_name = re.sub(r"\.[^.]+$", "", filename).strip() or None

        skills: list[str] = []
        for ln in lines:
            if re.match(r"^skills\b", ln, flags=re.IGNORECASE):
                parts = re.split(r"[:\-]", ln, maxsplit=1)
                if len(parts) == 2:
                    skills = [s.strip() for s in re.split(r",|\|", parts[1]) if s.strip()]
                break

        email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.IGNORECASE)
        phone_match = re.search(r"\+?\d[\d\s().-]{7,}\d", text)

        extracted_metadata: dict[str, Any] = {
            "filename": filename,
        }

        if doc_type == "cv":
            extracted_metadata.update(
                {
                    "name": extracted_name,
                    "email": email_match.group(0) if email_match else None,
                    "phone": phone_match.group(0) if phone_match else None,
                    "skills": skills,
                }
            )
        else:
            title = top_lines[0] if top_lines else None
            extracted_metadata.update(
                {
                    "title": title,
                    "summary": (" ".join(lines[:3])[:400] if lines else None),
                    "topics": [],
                }
            )

        return DocumentMetadataResult(
            doc_type=doc_type,
            extracted_name=extracted_name,
            extracted_metadata=extracted_metadata,
        )
