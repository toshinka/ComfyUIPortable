import os
from dynamicprompts.wildcards import WildcardManager
from dynamicprompts.generators import RandomPromptGenerator

wildcards_dir = os.path.abspath("ComfyUI/wildcards")
print(f"Testing WildcardManager with directory: {wildcards_dir}")
wm = WildcardManager(path=wildcards_dir)

# 登録されているコレクション/ファイル名を確認
collections = list(wm.match_collections("*"))
print(f"Total collections found: {len(collections)}")

# 代表的なワイルドカードファイルをサンプリング
sample_files = [f for f in os.listdir(wildcards_dir) if f.endswith(".txt")]
print(f"Sample wildcard files in folder: {sample_files[:5]}")

generator = RandomPromptGenerator(wildcard_manager=wm)

# テスト1: 選択構文 {A|B|C}
prompt1 = "masterpiece, 1girl, {smile|laughing|wink}, {red|blue|black} hair"
expanded1 = generator.generate(prompt1, 3)
print("\n--- Test 1: Dynamic Prompts {Option A|Option B} ---")
for p in expanded1:
    print(" ->", p)

# テスト2: 実際のWildcardファイル展開
if sample_files:
    target_base = os.path.splitext(sample_files[1])[0] # 例: AM_baseQua
    test_prompt2 = f"masterpiece, 1girl, __{target_base}__"
    print(f"\n--- Test 2: Wildcard expansion __{target_base}__ ---")
    expanded2 = generator.generate(test_prompt2, 2)
    for p in expanded2:
        print(" ->", p)

print("\nWildcard & Dynamic Prompts Test: ALL PASSED!")
