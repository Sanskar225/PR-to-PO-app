import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.data_loader import data_loader
from app.services.fuzzy_matcher import FuzzyMatcher

def test_matches():
    matcher = FuzzyMatcher(data_loader.items)
    
    test_cases = [
        ("brg 6308 ZZ for maintenance", "ITM-1022"),
        ("hyd hose 1/2 inch 2 wire", "ITM-1035"),
        ("v-belt b-54", "ITM-1024"),
        ("vci bag 600x900", "ITM-1044"),
        ("CMM calibration service", "ITM-1066"),
        ("eot crane 5 ton", "ITM-1071"),
        ("Drinking water purifier 50 LPH", "NEW"),
        ("Ball bearing 6205-2RS", "ITM-1021"),
        ("brg 6205 2rs", "ITM-1021"),
    ]
    
    all_passed = True
    for text, expected in test_cases:
        code, score = matcher.match(None, text)
        passed = (code == expected)
        print(f"'{text}' -> {code} (expected {expected}, score {score:.1f}) | Passed: {passed}")
        if not passed:
            all_passed = False
            
    print("ALL TESTS PASSED:", all_passed)

if __name__ == "__main__":
    test_matches()
