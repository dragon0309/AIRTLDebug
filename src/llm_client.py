"""LLM client for AIRTLDebug."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv


def _parse_json_response(text: str) -> dict[str, Any]:
    """Parse LLM JSON response; fall back to raw text if parsing fails."""
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "bug_summary": "Gemini generated RTL debug analysis.",
            "root_cause": text,
            "evidence": "See Gemini raw response.",
            "suggested_fix": "See Gemini raw response.",
            "confidence_score": "N/A",
            "raw_response": text,
        }

    return {
        "bug_summary": data.get("bug_summary", ""),
        "root_cause": data.get("root_cause", ""),
        "evidence": data.get("evidence", ""),
        "suggested_fix": data.get("suggested_fix", ""),
        "confidence_score": data.get("confidence_score", "N/A"),
        "raw_response": text,
    }


def _mock_analysis(intermediate: dict[str, Any]) -> dict[str, Any]:
    parsed = intermediate["parsed_failure"]
    gt = intermediate["ground_truth"]

    return {
        "bug_summary": (
            f"Signal {parsed['failed_signal']} mismatches at cycle "
            f"{parsed['failure_cycle']}."
        ),
        "root_cause": gt["root_cause"],
        "evidence": parsed["raw_failure_line"],
        "suggested_fix": gt["expected_fix"],
        "confidence_score": "High",
        "raw_response": "mock response",
    }


def _gemini_analysis(prompt: str) -> dict[str, Any]:
    load_dotenv(".env", override=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "bug_summary": "Gemini analysis was not executed.",
            "root_cause": "GEMINI_API_KEY is missing.",
            "evidence": "No external LLM API was called.",
            "suggested_fix": "Create a .env file with GEMINI_API_KEY.",
            "confidence_score": "N/A",
            "raw_response": "",
        }

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        text = response.text or ""
    except Exception as exc:  # noqa: BLE001
        return {
            "bug_summary": "Gemini analysis failed.",
            "root_cause": f"Gemini API error: {exc}",
            "evidence": "The prompt was built successfully, but the API call failed.",
            "suggested_fix": (
                "Use --model mock for reproducible demo, "
                "or check Gemini quota/billing."
            ),
            "confidence_score": "N/A",
            "raw_response": "",
        }

    return _parse_json_response(text)


def run_llm_analysis(
    intermediate: dict[str, Any],
    *,
    model: str = "mock",
    prompt: str | None = None,
) -> dict[str, Any]:
    """Return RTL debug analysis from mock or Gemini backend."""
    if model == "mock":
        return _mock_analysis(intermediate)

    if model == "gemini":
        if prompt is None:
            return {
                "bug_summary": "Gemini analysis was not executed.",
                "root_cause": "Prompt is missing.",
                "evidence": "No prompt was passed to the Gemini backend.",
                "suggested_fix": "Build a prompt before calling Gemini.",
                "confidence_score": "N/A",
                "raw_response": "",
            }
        return _gemini_analysis(prompt)

    return {
        "bug_summary": "LLM analysis was not executed.",
        "root_cause": f"Model `{model}` is not implemented.",
        "evidence": "No external LLM API was called.",
        "suggested_fix": "Use --model mock or --model gemini.",
        "confidence_score": "N/A",
        "raw_response": "",
    }
