#!/usr/bin/env python3
"""
Script de vérification de la structure du projet
Vérifie que tous les modules peuvent être importés correctement
"""
import sys

def test_imports():
    """Test que tous les modules peuvent être importés"""
    print("🔍 Vérification des imports...\n")

    tests = [
        ("Config", "from config.settings import VEEC_COLOR, ADVERSE_COLOR"),
        ("Models", "from src.models.state import get_initial_state"),
        ("Utils - Helpers", "from src.utils.helpers import clean_formations"),
        ("Utils - Rotation", "from src.utils.rotation import appliquer_rotation_veec"),
        ("Utils - Libero", "from src.utils.libero import swap_liberos_on_bench"),
        ("Components - Court", "from src.components.court import create_court_figure"),
        ("Components - Tables", "from src.components.tables import create_historique_table"),
        ("Components - Cards", "from src.components.cards import create_player_card"),
        ("App", "from app import app"),
    ]

    success = 0
    failures = []

    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
            success += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failures.append((name, str(e)))

    print(f"\n{'='*50}")
    print(f"Résultats: {success}/{len(tests)} imports réussis")

    if failures:
        print(f"\n⚠️  Échecs détectés:")
        for name, error in failures:
            print(f"  - {name}: {error}")
        return False
    else:
        print("\n✨ Tous les imports fonctionnent correctement !")
        return True

def test_initial_state():
    """Test que l'état initial peut être créé"""
    print("\n🔍 Vérification de l'état initial...\n")

    try:
        from src.models.state import get_initial_state
        state = get_initial_state()

        required_keys = [
            'formation_actuelle', 'joueurs_banc', 'score_veec',
            'score_adverse', 'liberos_veec', 'historique_stats'
        ]

        for key in required_keys:
            if key in state:
                print(f"✅ Clé '{key}' présente")
            else:
                print(f"❌ Clé '{key}' manquante")
                return False

        print("\n✨ État initial valide !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création de l'état: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("="*50)
    print("VÉRIFICATION DE LA STRUCTURE VEEC SCORER")
    print("="*50 + "\n")

    imports_ok = test_imports()
    state_ok = test_initial_state()

    print("\n" + "="*50)
    if imports_ok and state_ok:
        print("✨ Vérification réussie ! La structure est correcte.")
        print("="*50)
        return 0
    else:
        print("⚠️  Des problèmes ont été détectés.")
        print("="*50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
