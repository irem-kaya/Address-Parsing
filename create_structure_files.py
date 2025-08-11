from pathlib import Path

BASE = Path(__file__).resolve().parent  # <- scriptin olduğu klasör

files = {
    "addresskit/__init__.py": '"""AddressKit package initialization."""\n',
    "addresskit/normalize.py": '''"""
Normalize module for address processing.
"""
def normalize_address(input_path, output_path, config_path):
    print(f"Normalizing {input_path} -> {output_path} using {config_path}")
''',
    "addresskit/match.py": '''"""
Matching module for address data.
"""
def match_addresses(left_path, right_path, output_path, config_path):
    print(f"Matching {left_path} with {right_path} -> {output_path} using {config_path}")
''',
    "tests/test_normalize.py": """from addresskit.normalize import normalize_address

def test_normalize_address():
    assert callable(normalize_address)
""",
    "scripts/train.py": """if __name__ == "__main__":
    print("Training pipeline started...")
""",
    "scripts/eval.py": """if __name__ == "__main__":
    print("Evaluation pipeline started...")
""",
}

for rel, content in files.items():
    p = BASE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

print("✅ Dosyalar oluşturuldu:", BASE)
