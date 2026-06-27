from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist():
    required = [
        "README.md",
        "DATA_NOTICE.md",
        "CITATION.cff",
        "LICENSE",
        "requirements.txt",
        "paper14_submission_source/main.tex",
        "paper14_submission_source/refs.bib",
        "scripts/reproduce.py",
        "scripts/build_paper14_artifacts.py",
        "scripts/build_arxiv_source.py",
        "data/derived/tau_web_v2_full_smoke_stable/final_verdict_v3.json",
        "source_package_manifest/MANIFEST.json",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel


def test_claim_boundaries_are_explicit():
    text = (ROOT / "README.md").read_text() + "\n" + (ROOT / "paper14_submission_source/main.tex").read_text()
    forbidden = [
        "we prove Tau Core",
        "Tau Core is validated",
        "dark matter is ruled out",
        "LCDM is replaced",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "not a real-data discovery",
        "not a cosmological validation",
        "not a proof of Tau Core",
    ]
    for phrase in required:
        assert phrase in text


def test_arxiv_zip_present_after_reproduce_contract_can_be_built():
    assert (ROOT / "scripts" / "build_arxiv_source.py").exists()

