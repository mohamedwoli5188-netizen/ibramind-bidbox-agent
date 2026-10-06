# Evaluations

The public demo uses synthetic procurement data only.

1. E01 Synthetic-data gate: SYN-* is accepted.
2. E02 Requirement fixture: four requirements are present.
3. E03 Missing bid security: unresolved requirement is detected.
4. E04 Registration evidence: matched to R2.
5. E05 Method statement: matched to R3.
6. E06 Experience evidence: matched to R4.
7. E07 Personal-data check: no email/personal record in fixture.
8. E08 Award-safety check: no winner or award decision.
9. E09 Known unresolved failure: mandatory bid-security evidence is deliberately absent.

The ninth test is intentionally retained as an expected failure. The agent must surface this gap instead of inventing evidence or silently resolving it.

Run:

    python3 -m unittest -v tests/test_demo.py
