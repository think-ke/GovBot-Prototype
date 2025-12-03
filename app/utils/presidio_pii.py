"""
Presidio-powered PII analysis and anonymization helpers.

This module wraps Presidio's AnalyzerEngine and AnonymizerEngine
to provide simple functions for analyzing and redacting text.

It is designed to be used by higher-level helpers in `pii.py`
to preserve backward-compatible APIs across the app.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_anonymizer.entities.engine.recognizer_result import (
	RecognizerResult as AnonymizerRecognizerResult,
)


@lru_cache(maxsize=1)
def _get_analyzer() -> AnalyzerEngine:
	"""Return a singleton AnalyzerEngine instance.

	Uses spaCy by default (en_core_web_lg is listed in requirements).
	"""
	return AnalyzerEngine()


@lru_cache(maxsize=1)
def _get_anonymizer() -> AnonymizerEngine:
	"""Return a singleton AnonymizerEngine instance."""
	return AnonymizerEngine()


def analyze_text(
	text: str,
	*,
	language: str = "en",
	entities: Optional[List[str]] = None,
	score_threshold: Optional[float] = 0.3,
	allow_list: Optional[List[str]] = None,
) -> List[RecognizerResult]:
	"""Run Presidio analysis and return recognizer results.

	Args:
		text: Input text to scan.
		language: Language code understood by Presidio's NLP engine.
		entities: Optional subset of entities to detect. If None, detect all.
		score_threshold: Minimum confidence score to include.
		allow_list: Words/regex to allow and skip.

	Returns:
		List of RecognizerResult spans.
	"""
	if not text:
		return []
	analyzer = _get_analyzer()
	results: List[RecognizerResult] = analyzer.analyze(
		text=text,
		language=language,
		entities=entities,
		score_threshold=score_threshold,
		allow_list=allow_list,
	)
	return results or []


def anonymize_text(
	text: str,
	recognizer_results: Iterable[RecognizerResult],
	*,
	placeholder_format: str = "<{entity_type}_REDACTED>",
	operators_override: Optional[Dict[str, OperatorConfig]] = None,
) -> Tuple[str, List[Dict[str, object]]]:
	"""Anonymize text given Presidio recognizer results.

	Args:
		text: Original text.
		recognizer_results: Iterable of RecognizerResult from analyze_text.
		placeholder_format: Format string for replacement text per entity type.
		operators_override: Optional explicit operators mapping per entity type.

	Returns:
		Tuple of (redacted_text, items) where items is the anonymizer items list.
	"""
	anonymizer = _get_anonymizer()
	results_list = list(recognizer_results or [])
	if not text or not results_list:
		return text, []

	# Convert analyzer results to anonymizer results class to satisfy typing
	anon_results: List[AnonymizerRecognizerResult] = [
		AnonymizerRecognizerResult(
			entity_type=r.entity_type, start=r.start, end=r.end, score=r.score
		)
		for r in results_list
	]

	if operators_override is None:
		# Build operator config per entity type to replace with placeholders.
		entity_types = {r.entity_type for r in results_list}
		operators_override = {
			et: OperatorConfig(
				"replace", {"new_value": placeholder_format.format(entity_type=et)}
			)
			for et in entity_types
		}

	engine_result = anonymizer.anonymize(
		text=text, analyzer_results=anon_results, operators=operators_override
	)
	# engine_result.items is a list of OperatorResult; provide dicts for convenience
	items = [i.to_dict() for i in engine_result.items]
	return engine_result.text, items


def redact_text(
	text: str,
	*,
	language: str = "en",
	entities: Optional[List[str]] = None,
	score_threshold: Optional[float] = 0.3,
	allow_list: Optional[List[str]] = None,
	placeholder_format: str = "<{entity_type}_REDACTED>",
) -> Tuple[str, List[RecognizerResult]]:
	"""Analyze and redact text in one go using Presidio.

	Returns redacted text and the underlying RecognizerResult list.
	"""
	results = analyze_text(
		text,
		language=language,
		entities=entities,
		score_threshold=score_threshold,
		allow_list=allow_list,
	)
	redacted, _ = anonymize_text(
		text, results, placeholder_format=placeholder_format
	)
	return redacted, results

