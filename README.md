# ComfyUI Play Prompt Output Node

プレイ内容から **Shot1 / Shot2** ほか複数ピンを出力するノードです。  
パッケージ内の **全 `prompts*.json` を自動マージ**します。

## 特徴

| 項目 | 内容 |
|------|------|
| プレイモード | `select` / `random` |
| 男性タイプ | `select` / `random`（`{male}` 置換） |
| パターン | 1プレイに複数ある場合は **パターンは常にランダム** |
| シード | 実行のたびに再ランダム |
| 複数 JSON | `prompts.json`, `prompts_positions.json`, `prompts_foreplay.json`, `prompts_scenarios.json` など `prompts*.json` をすべて読込 |

## 出力ピン

| ピン | 内容 |
|------|------|
| Shot1 | 開始・主動作（原則まだ射精しない） |
| Shot2 | 変化・クライマックス（射精するパターンはここでいつ/中外/本数/着弾） |
| Dialogue_Shot1 / Dialogue_Shot2 | 日本語セリフ（短い） |
| overall_soundscape | 動作に対応する音 |
| summary_action | 全体の動き要約 |
| camera_lock | 構図固定 |
| negative | 禁止事項（photorealistic 等含む） |
| play_name / pattern_id / male_type_name / used_seed | メタ |

## プロンプト方針（v5）

- **視点・アングル**を Shot 冒頭で明示（三人称具体アングルが基本、POV は明示時のみ）
- **位置関係**（誰が前/後ろ/上、手の位置、支え）を明記
- **射精**は Shot2 専用。トリガー・中か外・本数・着弾・射精中の腰をセットで書く
- 見えるペニスは **forcefully erect**
- 画風語・秒数なし。キャラ参照向けに negative へ photorealistic / pores

## インストール

```text
ComfyUI/custom_nodes/comfyui-play-prompt-node/
├── __init__.py
├── nodes.py
├── prompts.json
├── prompts_positions.json
├── prompts_foreplay.json
├── prompts_scenarios.json
├── pyproject.toml
└── README.md
```

JSON を追加・更新したあとは **ComfyUI 再起動**（または Reload ノード後に UI 再読込）してください。Combo の選択肢はスキーマ定義時に決まります。

## Reload ノード

`Reload Play Prompts JSON` でキャッシュを破棄し、全 `prompts*.json` を再読込します。件数とソースファイル名が status に出ます。
