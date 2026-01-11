# 借景 (Shakkei) - 遠景可視化プロジェクト

## プロジェクト概要

御茶ノ水ソラシティ21階からの眺望を3D可視化するシステム。PyVistaを用いて、近景の建物から遠景の富士山・筑波山までをリアルに再現します。

### ビジョン

- **視点**: 御茶ノ水ソラシティ21階（地上約70m）
- **近景**: PLATEAU建物データ（半径2-3km）
- **中距離**: 関東平野の地形（DEM）
- **遠景**: 筑波山（約60km）、富士山（約100km）
- **演出**: 距離依存フォグ、山岳ラベル、視線可視化

## 技術スタック

### コアライブラリ

```
pyvista >= 0.43.0        # 3D可視化エンジン
vtk >= 9.3.0              # VTK（フォグ機能）
numpy >= 1.24.0
```

### 地理空間処理

```
geopandas >= 0.14.0       # 空間データ処理
shapely >= 2.0.0          # ジオメトリ操作
pyproj >= 3.6.0           # 座標変換
rasterio >= 1.3.0         # ラスタデータ（DEM）
rioxarray >= 0.15.0       # xarray + rasterio
```

### データ取得

```
plateaupy                 # PLATEAU API（予定）
requests                  # HTTP通信
```

## システムアーキテクチャ

### データフロー

```
[データ取得層]
    ├─ PLATEAU API → 建物データ (CityGML)
    ├─ 国土地理院 → DEM (GeoTIFF)
    └─ 手動設定 → 観測点・山岳座標

[前処理層]
    ├─ 座標系統一 (EPSG:6677)
    ├─ CityGML → Mesh変換
    ├─ DEM → PyVista Grid
    └─ 建物軽量化 (LOD調整)

[可視化層]
    ├─ PyVista Plotter
    ├─ VTK Renderer (フォグ)
    ├─ カメラ制御
    └─ インタラクティブ操作

[演出層]
    ├─ 距離依存フォグ
    ├─ 山岳ラベル
    ├─ 視線ライン
    └─ 時間帯モード（朝/昼/夕）
```

### ディレクトリ構造

```
shakkei/
├─ README.md                     # このファイル
├─ requirements.txt              # 依存ライブラリ
├─ setup.py                      # パッケージ設定
│
├─ data/                         # データディレクトリ（Git管理外）
│  ├─ plateau/                   # PLATEAU建物データ
│  │  └─ ochanomizu/
│  │     └─ bldg/*.gml
│  ├─ dem/                       # 国土地理院DEM
│  │  └─ kanto_region.tif
│  └─ processed/                 # 前処理済みデータ
│     ├─ buildings.vtp
│     └─ terrain.vti
│
├─ src/
│  ├─ __init__.py
│  ├─ downloader/                # データダウンロード
│  │  ├─ __init__.py
│  │  ├─ plateau.py              # PLATEAU取得
│  │  └─ dem.py                  # DEM取得
│  │
│  ├─ preprocessor/              # データ前処理
│  │  ├─ __init__.py
│  │  ├─ coordinate.py           # 座標系変換
│  │  ├─ citygml_parser.py       # CityGML → Mesh
│  │  ├─ dem_processor.py        # DEM処理
│  │  └─ mesh_optimizer.py       # メッシュ軽量化
│  │
│  ├─ visualizer/                # 可視化
│  │  ├─ __init__.py
│  │  ├─ plotter.py              # PyVista制御
│  │  ├─ fog.py                  # VTKフォグ設定
│  │  ├─ camera.py               # カメラ制御
│  │  └─ effects.py              # 演出効果
│  │
│  ├─ config/                    # 設定
│  │  ├─ __init__.py
│  │  ├─ locations.py            # 座標定義
│  │  └─ rendering.py            # レンダリング設定
│  │
│  └─ main.py                    # エントリーポイント
│
├─ notebooks/                    # Jupyter開発用
│  ├─ 01_data_download.ipynb
│  ├─ 02_preprocessing.ipynb
│  ├─ 03_visualization.ipynb
│  └─ 04_fog_tuning.ipynb
│
└─ tests/                        # テスト
   ├─ test_coordinate.py
   ├─ test_parser.py
   └─ test_fog.py
```

## データソース

### 1. PLATEAU（建物データ）

- **提供元**: 国土交通省 Project PLATEAU
- **対象地域**: 東京都千代田区（御茶ノ水周辺 半径2-3km）
- **形式**: CityGML (LOD1 / LOD2)
- **取得方法**:
  - PLATEAU データポータル
  - または plateaupy API
- **座標系**: JGD2011 / 平面直角座標系IX (EPSG:6677)

### 2. DEM（地形データ）

- **提供元**: 国土地理院 基盤地図情報
- **対象範囲**: 関東平野全体（富士山～筑波山をカバー）
  - 西: 富士山周辺
  - 東: 筑波山周辺
  - 横幅: 約150-180km
- **形式**: GeoTIFF
- **解像度**: 10mメッシュ（標高）
- **座標系**: EPSG:6677に統一

### 3. 基準点座標（WGS84 → EPSG:6677変換）

| 地点 | 緯度 | 経度 | 標高 (m) | 距離 (km) |
|------|------|------|----------|-----------|
| 御茶ノ水ソラシティ | 35.6996 | 139.7645 | ~70 (21階) | - |
| 筑波山 | 36.2256 | 140.1064 | 877 | ~60 |
| 富士山 | 35.3606 | 138.7274 | 3776 | ~100 |

## 座標系とスケール

### 採用座標系

**EPSG:6677** (JGD2011 / 平面直角座標系 IX系)

- 対象地域: 関東一円
- 単位: メートル
- PyVista内: 1 unit = 1 m

### 統一の重要性

全データをEPSG:6677に統一することで:

- 距離計算が単純（ユークリッド距離）
- フォグパラメータが直感的（m単位）
- 視線遮蔽判定が正確

## 実装フェーズ

### Phase 1: 座標系の確立

**目的**: 全データを統一座標系で扱える状態にする

1. PLATEAU建物をEPSG:6677に変換
2. DEMをEPSG:6677に変換
3. 基準点（ソラシティ、富士山、筑波山）の座標を同一系に統一
4. 座標変換ユーティリティの実装

**成果物**: `src/preprocessor/coordinate.py`

### Phase 2: 地形（DEM）の読み込みと処理

**目的**: 広域地形を扱えるようにする

1. 国土地理院DEMのダウンロード（150-180km四方）
2. GeoTIFF → PyVista Grid変換
3. 高さの誇張処理（factor=1.2-1.5）
4. メモリ最適化（必要に応じてダウンサンプリング）

**実装ポイント**:
```python
terrain = pv.read("kanto_dem.vti")
terrain = terrain.warp_by_scalar(factor=1.5)  # 誇張
```

**成果物**: `src/preprocessor/dem_processor.py`

### Phase 3: 建物データの取得と軽量化

**目的**: 近景建物を表示可能にする

1. PLATEAUデータダウンロード（千代田区、半径2-3km）
2. CityGML → OBJ / Mesh変換
3. LOD調整とポリゴン削減
4. Z方向正規化（地面を0に）

**実装ポイント**:
```python
buildings = pv.read("plateau_ochanomizu.obj")
zmin = buildings.bounds[4]
buildings.translate((0, 0, -zmin), inplace=True)
```

**成果物**:
- `src/downloader/plateau.py`
- `src/preprocessor/citygml_parser.py`
- `src/preprocessor/mesh_optimizer.py`

### Phase 4: カメラと視線の設定

**目的**: ソラシティ21階視点を再現

1. 観測点座標の設定（ソラシティ21階、地上70m）
2. カメラ方向の制御（富士山方向 / 筑波山方向）
3. 視野角・クリッピング範囲の調整
4. インタラクティブ操作の実装

**実装ポイント**:
```python
observer = [x_solacity, y_solacity, z_ground + 70]
plotter.camera_position = [observer, fuji_pos, (0, 0, 1)]
plotter.camera.clipping_range = (1, 150_000)  # 1m～150km
```

**成果物**: `src/visualizer/camera.py`

### Phase 5: フォグの実装

**目的**: 距離依存の大気効果を再現

1. VTK Rendererを直接操作
2. フォグモード選択（Linear / Exponential / Exponential²）
3. パラメータチューニング（密度、色、範囲）
4. 天候モード切替（晴天 / 曇天 / 夕方）

**実装ポイント**:
```python
ren = plotter.renderer
ren.SetFogModeToExponential()
ren.SetFogDensity(0.000015)  # 晴天・冬
ren.SetFogColor(0.8, 0.85, 0.9)  # 薄青
```

**フォグパラメータ目安**:

| 天候 | Fog Mode | Density | 筑波山(60km) | 富士山(100km) |
|------|----------|---------|--------------|---------------|
| 晴天・冬 | Exponential | 0.000015 | ◎ 明瞭 | ○ 見える |
| 晴天・夏 | Exponential | 0.000025 | ○ 見える | △ かすか |
| 曇天 | Exponential | 0.000040 | △ かすか | × 見えない |

**成果物**: `src/visualizer/fog.py`

### Phase 6: 演出と最終調整

**目的**: わかりやすく美しい表示

1. 山岳ラベルの配置（富士山、筑波山）
2. 視線ラインの描画（ソラシティ→山）
3. 時間帯モード（朝日、夕焼け、夜景）
4. UIコントロール（フォグ調整スライダーなど）

**実装ポイント**:
```python
# 山岳ラベル
plotter.add_point_labels(
    [fuji_pos, tsukuba_pos],
    ["富士山 (100km)", "筑波山 (60km)"],
    font_size=28
)

# 視線ライン
line = pv.Line(observer, fuji_pos)
plotter.add_mesh(line, color="yellow", opacity=0.3)
```

**成果物**: `src/visualizer/effects.py`

## 技術的考慮事項

### メモリとパフォーマンス

- **地形データ**: 150km四方の10mメッシュは大量メモリを消費
  - 必要に応じて解像度を下げる（20m、50mメッシュ）
  - 視点から遠い領域は低LOD化

- **建物データ**: PLATEAUは高精度すぎる場合がある
  - ポリゴン削減ツール（Blender、MeshLab）を活用
  - LOD1とLOD2を使い分け

### 座標変換の精度

- WGS84 → EPSG:6677変換は `pyproj` で実施
- 数十〜数百kmのスケールでは投影歪みに注意
- 平面直角座標系の適用範囲を理解する

### VTKフォグの制限

- フォグはカメラからの距離に基づく
- オブジェクトごとのフォグ設定は不可
- 色は単色のみ（グラデーション不可）
- `clipping_range` との相互作用に注意

### 視線遮蔽判定（将来拡張）

Phase 1-6では実装しないが、将来的には:

- レイキャスティングで建物による遮蔽を判定
- 「富士山が見える日」のシミュレーション
- 最適視点の自動計算

## 開発環境

### 必須

- Python 3.10+
- pip or conda

### 推奨

- Jupyter Lab（開発・パラメータ調整）
- Git LFS（大容量データ管理）
- GPU（大規模メッシュのレンダリング高速化）

### インストール

```bash
# リポジトリクローン
git clone https://github.com/yourusername/shakkei.git
cd shakkei

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存ライブラリインストール
pip install -r requirements.txt

# データディレクトリ作成
mkdir -p data/{plateau,dem,processed}
```

## 使用方法（予定）

### 基本実行

```bash
python src/main.py
```

### Jupyter開発

```bash
jupyter lab
# notebooks/03_visualization.ipynb を開く
```

### カスタマイズ例

```python
from src.visualizer import Plotter
from src.config import SOLACITY, FUJI, TSUKUBA

plotter = Plotter(viewpoint=SOLACITY)
plotter.add_buildings("data/processed/buildings.vtp")
plotter.add_terrain("data/processed/terrain.vti", warp_factor=1.5)
plotter.set_fog(mode="exponential", density=0.000015, color=(0.8, 0.85, 0.9))
plotter.look_at(FUJI)
plotter.show()
```

## プロジェクト管理

### マイルストーン

- [ ] M1: データ取得環境構築
- [ ] M2: 座標系統一と前処理パイプライン
- [ ] M3: 基本的な3D表示（建物+地形）
- [ ] M4: フォグ実装と遠景表示
- [ ] M5: 演出機能とUI改善
- [ ] M6: デモ完成・ドキュメント整備

### 開発優先順位

1. **Phase 1**: 座標系 → すべての基盤
2. **Phase 3**: 建物表示 → 早期視覚フィードバック
3. **Phase 2**: 地形 → スケール感の確立
4. **Phase 5**: フォグ → プロジェクトの核心
5. **Phase 4, 6**: カメラ・演出 → 最終仕上げ

## 参考資料

### 公式ドキュメント

- [PyVista Documentation](https://docs.pyvista.org/)
- [VTK User's Guide](https://vtk.org/documentation/)
- [PLATEAU](https://www.mlit.go.jp/plateau/)
- [国土地理院 基盤地図情報](https://fgd.gsi.go.jp/)

### 技術ブログ・チュートリアル

- PyVistaでのフォグ実装例
- PLATEAU CityGMLパース手法
- 大規模DEMの効率的な読み込み

## ライセンス

MIT License

### データライセンス

- PLATEAU: [PLATEAU Policy](https://www.mlit.go.jp/plateau/site-policy/)に準拠
- 国土地理院DEM: 測量法に基づく利用規約に準拠

## 貢献

Issue、Pull Requestを歓迎します。

## 作成者

Tetsuo Koyama

## 更新履歴

- 2026-01-11: プロジェクト設計初版
