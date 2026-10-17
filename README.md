# ComfyUI Play Prompt Output Node

プレイ内容から **Shot1 / Shot2** の英語プロンプトを出力するノードです。  
**男性の種類**（黒人・太った・老いた・筋肉質など）を選択 / ランダムで切り替え可能です。

## 特徴

| 項目 | 内容 |
|------|------|
| プレイモード | `select`（指定） / `random`（全プレイからランダム） |
| 男性タイプモード | `select` / `random` |
| パターン | 1プレイに複数パターンがある場合、**selectでもパターンはランダム** |
| プレースホルダ | プロンプト内の `{male}` を選んだ男性描写に置換 |
| シード | 実行のたびにランダムに変化 |
| 出力 | Shot1, Shot2, play_name, pattern_id, male_type_name, used_seed |

## インストール

```text
ComfyUI/custom_nodes/
└── comfyui-play-prompt-node/
    ├── __init__.py
    ├── nodes.py
    ├── prompts.json      ← プレイリスト & 男性タイプをここに書く
    ├── pyproject.toml
    └── README.md
```

## prompts.json 構造

### male_types（男性の種類）

```json
"male_types": [
  {
    "id": "black",
    "name": "Black man",          // Comboに表示
    "prompt": "a Black man"       // {male} に差し込まれる英語フレーズ
  },
  {
    "id": "fat",
    "name": "Fat man",
    "prompt": "a fat, overweight man"
  },
  {
    "id": "old",
    "name": "Old man",
    "prompt": "an elderly man"
  },
  {
    "id": "muscular",
    "name": "Muscular man",
    "prompt": "a muscular, athletic man"
  }
  // ... 自由に追加
]
```

### plays（プレイ）

```json
"plays": [
  {
    "id": "unique_id",
    "name": "表示名",
    "description": "任意",
    "patterns": [
      {
        "id": "pattern_1",
        "shot1": "{male} sitting on a chair, reading a book, soft light, medium shot",
        "shot2": "{male} sitting on a chair, looking up from the book, soft light, medium shot"
      }
    ]
  }
]
```

- `{male}` があるパターン → 選んだ男性タイプが挿入される  
- `{male}` がないパターン → 男性タイプ設定は無視される（女性のみのプレイなど）

## ノード入力

| 入力 | 説明 |
|------|------|
| mode | プレイの select / random |
| play | プレイ名（mode=select 時） |
| male_mode | 男性タイプの select / random |
| male_type | 男性タイプ名（male_mode=select 時） |
| seed | ベースシード（実行ごとに内部再ランダム化） |

## 出力

| ピン | 型 | 内容 |
|------|-----|------|
| Shot1 | STRING | ショット1プロンプト（{male} 置換済み） |
| Shot2 | STRING | ショット2プロンプト |
| play_name | STRING | 選ばれたプレイ名 |
| pattern_id | STRING | 選ばれたパターンID |
| male_type_name | STRING | 選ばれた男性タイプ名 |
| used_seed | INT | 実際に使われたシード |

## 付属の男性タイプ（雛形）

| name | prompt |
|------|--------|
| Average man | an average-looking man |
| Black man | a Black man |
| White man | a White man |
| Asian man | an Asian man |
| Fat man | a fat, overweight man |
| Thin man | a thin, slender man |
| Muscular man | a muscular, athletic man |
| Old man | an elderly man |
| Young man | a young man |
| Middle-aged man | a middle-aged man |
| Bald man | a bald man |
| Bearded man | a bearded man |

必要に応じて `prompts.json` の `male_types` に追加・編集してください。

## 注意

- 現在のプレイ内容は**雛形**です。あとで実際のリストを渡してください。
- プロンプトは英語で書いてください。
- 男性が登場しないプレイでは `{male}` を使わないでください。
