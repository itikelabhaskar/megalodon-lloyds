from knowledge_bank.kb_manager import get_kb_manager

kb = get_kb_manager()
patterns = kb.get_all_patterns()

print(f'Knowledge Bank loaded: {len(patterns)} patterns')
print()

for p_id, p_data in list(patterns.items())[:3]:
    print(f'Pattern: {p_id}')
    print(f'  Description: {p_data["description"]}')
    print(f'  Fixes: {len(p_data["historical_fixes"])}')
    print()

print("✅ Knowledge Bank is working!")
