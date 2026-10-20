# Five Walls Deployment Checklist for 2027

**論文補足資料**：Generative AI in Student–Nurse Clinical Communication: A Multi-LLM In-Silico Evaluation and Five Walls to 2027

**対象読者**：医療機関・看護教育機関の IT 部門、臨床安全委員会、看護教育担当者

**用途**：本論文の Five Walls フレームワークを、施設の AI 導入意思決定で **即座に使えるチェックリスト形式** に翻案したもの。各 wall に対し、deployment 前に確認すべき具体項目を列挙。すべての項目に「Yes / No / N/A」で回答し、すべての Critical 項目が Yes となるまで deployment しないことを推奨。

**バージョン**：v1.1（公開版）

---

## Wall 1: Trust（信頼の壁）

学生・看護師・患者が AI 介在を受容する条件が整っているか。

### Critical（必須）

- [ ] 学生に対し、AI が会話に介在することが事前に開示されているか
- [ ] 学生に AI 介入を拒否する権利が文書で保証されているか
- [ ] AI 介在を拒否した学生が、教育・評価上の不利益を被らない制度設計があるか
- [ ] 看護師（preceptor）に対し、AI が student message を edit する場合がある旨が開示されているか
- [ ] 患者（実臨床応用時）に対し、担当看護師の student が AI 介在下にある旨を告知する制度があるか

### Recommended（推奨）

- [ ] 学生が「AI 介在の有無」を session ごとに選択できる UI が用意されているか
- [ ] 介在ログ（誰の発言を AI がどう edit したか）を学生本人が確認できるか
- [ ] AI 介在による学生の主観的受容度（feel heard ratio など）を定期測定する仕組みがあるか

### 根拠

Yin et al. (2024) は AI 生成メッセージを「AI 由来」と認識した受信者の "feel heard" 評価が有意に低下することを示している。本論文 §5.1 参照。

---

## Wall 2: Privacy（プライバシーの壁）

臨床情報を含む通信が法的に保護されているか。

### Critical（必須）

- [ ] AI ベンダー（API 提供者）が施設の **データ処理者（data processor）** として法的に位置づけられているか
- [ ] 日本における APPI（個人情報保護法）の **要配慮個人情報** 取扱要件を満たしているか
- [ ] 国際施設の場合、GDPR Article 9（特別カテゴリーデータ）への準拠経路が確立されているか
- [ ] HIPAA 適用施設の場合、BAA（Business Associate Agreement）が AI ベンダーと締結されているか
- [ ] 患者情報を API に送信する場合、de-identification の手順が文書化されているか
- [ ] API call ログの保存期間・廃棄手順が文書化されているか

### Recommended（推奨）

- [ ] AI ベンダーが「学習に使用しない」と契約上明記しているか（Anthropic, OpenAI Enterprise, Google Vertex AI などは標準で対応）
- [ ] On-premise / private cloud deployment の検討状況が記録されているか
- [ ] 患者の同意撤回時に、過去の AI session log を削除する手順があるか

### 根拠

本論文 §5.2 では研究用合成データを 3 商用 API に送信した。実臨床応用時は本質的に異なる法的構造を要する。

---

## Wall 3: Over-reliance（過依存の壁）

学生・看護師が AI に依存しすぎず、自己の能力を発達させられるか。

### Critical（必須）

- [ ] AI 介入を **段階的に減らす** scaffolding 設計が curriculum に組み込まれているか
- [ ] 学生が AI なしでも臨床コミュニケーションを行える能力評価（formative + summative）が定期実施されるか
- [ ] AI 介入の効果が「学習の displacement（置換）」ではなく「学習の facilitation（促進）」となっているかを評価する指標があるか
- [ ] 看護師が AI のアラート/提案を **自動承認せず批判的に評価する** 訓練を受けているか

### Recommended（推奨）

- [ ] 学生に AI 出力の品質を自己評価させる reflection 課題が組み込まれているか
- [ ] 「AI なしで X 回連続して質の高い SBAR 報告ができたら次段階へ」のような scaffolding 基準があるか
- [ ] AI 介入頻度の longitudinal monitoring（学生ごと、学期ごと）が実施されるか

### 根拠

本論文 §5.3 では Student Support（学生側 turn-by-turn coaching）が全 3 アクター LLM で効果不在を示した。これは scaffolding 理論に整合する構造的所見。

---

## Wall 4: Competency（臨床能力の壁）

AI 介入が臨床的に安全な範囲に留まっているか。

### Critical（必須）

- [ ] AI 出力に対する **臨床内容の独立審査（content adjudication）** プロセスが定義されているか
- [ ] 投薬量範囲、症状解釈、SBAR 内容、escalation 判断について、AI 出力の **臨床正確性** が施設内専門家によって定期検証されているか
- [ ] Hallucination（事実誤認生成）の検出基準・対応プロトコルがあるか
- [ ] Acute handover（急性期申し送り、本論文 S3 シナリオに相当）において、AI 介入の latency（応答遅延）が許容範囲内か
- [ ] AI が学生・看護師の発言から「uncertainty marker（迷い・不確実性の指標）」を **smoothing せず保持する** 設計になっているか

### Recommended（推奨）

- [ ] 施設内に AI 出力品質モニタリング委員会（quarterly review 等）があるか
- [ ] 重大な臨床判断（escalation など）が関わる場合は AI 介入を一時停止する mechanism があるか
- [ ] AI 介入下での near-miss / adverse event 記録システムがあるか

### 根拠

本論文 §5.4 では Judge LLM が communication 品質を評価したが、**clinical accuracy は測定していない**。これは deployment 前に独立評価される必要がある。

---

## Wall 5: Governance（ガバナンスの壁）

責任の所在と model 変更管理が明確か。

### Critical（必須）

- [ ] AI 介入下での誤判定が患者害を引き起こした場合の **責任の所在** が文書化されているか（看護師／施設／AI ベンダーの分担）
- [ ] AI モデルが更新（version up、deprecation）された場合の **再評価プロトコル** があるか
- [ ] 複数 LLM を使い分ける場合、各モデルの選択根拠が文書化されているか
- [ ] LLM 選択を単一の IT 担当者の判断ではなく、**臨床安全委員会と教育担当の合議** で決定する制度があるか
- [ ] 本論文の主要所見（actor-model variance ε² = 0.49 が intervention-condition variance ε² = 0.12 を上回る）が施設内 LLM 評価に反映されているか
- [ ] IRB（または同等の倫理審査委員会）の承認が、deployment phase に対して取得されているか

### Recommended（推奨）

- [ ] 日本看護協会の AI 関連ガイドライン（最新版）への準拠が確認されているか
- [ ] 国際的な医療 AI 規制（EU AI Act、FDA SaMD など）への対応経路が記録されているか
- [ ] AI ベンダーの SLA（Service Level Agreement）に、医療応用に必要な可用性・応答時間要件が含まれているか
- [ ] 教育部門・IT 部門・臨床部門の責任者が定期的に AI deployment review を行う場が制度化されているか

### 根拠

本論文 §5.5 で詳述。本研究実施期間中にも主要 actor LLM が provider によって retire されており、temporal instability は実証済。また論文の Practice 4（§5.6）は、臨床発言を書き換える介入に対し、数値・単位・患者識別子の決定論的な整合チェックを推奨している。導入施設は本 Wall に追加してよい。

---

## 統合チェックリスト：Deployment 可否判定

| Wall | Critical 項目数 | 達成数 | 達成率 |
|------|----------------|--------|--------|
| 1. Trust | 5 | __/5 | __% |
| 2. Privacy | 6 | __/6 | __% |
| 3. Over-reliance | 4 | __/4 | __% |
| 4. Competency | 5 | __/5 | __% |
| 5. Governance | 6 | __/6 | __% |
| **合計** | **26** | __/26 | __% |

### Deployment 判定基準

| Critical 達成率 | 判定 | アクション |
|----------------|------|----------|
| 100% | **GO**：deployment 開始可 | パイロット段階へ進行 |
| 80–99% | **CONDITIONAL**：未達成項目に対する mitigation plan が必要 | 施設内倫理委員会で個別評価 |
| 50–79% | **HOLD**：major preparation が必要 | 未達成項目を 3 ヶ月以内に解消する計画策定 |
| 0–49% | **NO-GO**：deployment 不可 | 制度設計段階に差し戻し |

---

## 改訂履歴

| Version | 日付 | 変更内容 |
|---------|------|---------|
| 1.0 | 2026-05-20 | 初版（本論文補足資料） |
| 1.1 | 公開時 | 効果量の記号を論文に合わせ η² → ε²（rank epsilon-squared）に修正。ライセンス表記をリポジトリ全体（MIT）に統一。著者名の誤記を修正。Wall 5 の根拠に論文 Practice 4 への言及を追加。英語版（deployment_checklist.md）を追加 |

---

## ライセンス

本チェックリストは本論文に付随する補足資料として、リポジトリ全体と同じ MIT License の下で公開される（LICENSE 参照）。再利用時は本論文の引用を求める：Tajima, H.: Generative AI in Student–Nurse Clinical Communication: A Multi-LLM In-Silico Evaluation and Five Walls to 2027, Journal of Information Processing, Vol.35 (2027).

## 連絡先

田島 博之（秀明大学看護学部）  
tajima@mailg.shumei-u.ac.jp
