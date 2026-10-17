"""CrewAI crews for the ATC MAS.

Each crew package separates ``agents.py``, ``tasks.py`` and ``crew.py``
(plain-Python CrewAI pattern). Crews are only *built* on demand by the
``build_*_crew()`` factories; building does not call an LLM, ``kickoff()``
does. The deterministic CLI and tests never kick off a crew.

Crews:

1. ``data_management``       — load, validate, normalise inputs.
2. ``surveillance_conflict`` — run deterministic detection, summarise findings.
3. ``tactical_resolution``   — maneuver proposal/validation (INCOMPLETE).
4. ``reporting``             — compose a narrative report summary.
"""
