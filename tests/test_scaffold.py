"""Smoke test ensuring repo scaffold is importable."""


def test_scaffold_imports() -> None:
    import src.case_loader  # noqa: F401
    import src.log_parser  # noqa: F401
    import src.rtl_debug_agent  # noqa: F401
    import src.rtl_extractor  # noqa: F401
    import src.sim_runner  # noqa: F401
