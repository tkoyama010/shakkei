"""
可視化モジュールのCLIエントリーポイント.

使用方法:
    python -m src.visualizer
"""

import argparse
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pyvista as pv

logger = logging.getLogger(__name__)

# CityGML名前空間
NAMESPACES = {
    "core": "http://www.opengis.net/citygml/2.0",
    "bldg": "http://www.opengis.net/citygml/building/2.0",
    "gml": "http://www.opengis.net/gml",
}


def parse_pos_list(pos_list_text: str) -> np.ndarray:
    """
    gml:posListテキストから座標配列を抽出.

    Parameters
    ----------
    pos_list_text : str
        空白区切りの座標値テキスト

    Returns
    -------
    np.ndarray
        (N, 3)の座標配列

    """
    coords = list(map(float, pos_list_text.split()))
    return np.array(coords).reshape(-1, 3)


def parse_building_lod1(building_elem: ET.Element) -> pv.PolyData | None:
    """
    建物要素からLOD1の3D形状を抽出.

    Parameters
    ----------
    building_elem : ET.Element
        建物のXML要素

    Returns
    -------
    pv.PolyData | None
        建物のメッシュ、抽出できない場合はNone

    """
    # LOD1 Solidを検索
    lod1_solid = building_elem.find(".//bldg:lod1Solid", NAMESPACES)
    if lod1_solid is None:
        return None

    # 全てのPolygonを検索
    polygons = lod1_solid.findall(".//gml:Polygon", NAMESPACES)

    if not polygons:
        return None

    all_points = []
    all_faces = []
    point_offset = 0

    for polygon in polygons:
        # 外側の境界（exterior）を取得
        pos_list = polygon.find(".//gml:posList", NAMESPACES)
        if pos_list is None or pos_list.text is None:
            continue

        points = parse_pos_list(pos_list.text)

        # 最後の点は最初の点と同じ（閉じたループ）なので除外
        if len(points) > 0 and np.allclose(points[0], points[-1]):
            points = points[:-1]

        num_points = len(points)
        if num_points < 3:  # noqa: PLR2004
            continue

        # 面を作成
        face = [num_points, *range(point_offset, point_offset + num_points)]

        all_points.extend(points)
        all_faces.append(face)
        point_offset += num_points

    if not all_points:
        return None

    # PyVistaメッシュを作成
    points_array = np.array(all_points)
    faces_array = np.hstack(all_faces)

    mesh = pv.PolyData(points_array, faces=faces_array)
    return mesh


def parse_citygml_file(gml_file: Path) -> list[pv.PolyData]:
    """
    CityGMLファイルから建物メッシュのリストを抽出.

    Parameters
    ----------
    gml_file : Path
        CityGMLファイルのパス

    Returns
    -------
    list[pv.PolyData]
        建物メッシュのリスト

    """
    try:
        tree = ET.parse(gml_file)
        root = tree.getroot()

        buildings = root.findall(".//bldg:Building", NAMESPACES)
        logger.debug(f"{gml_file.name}: {len(buildings)}棟の建物を検出")

        meshes = []
        for building in buildings:
            mesh = parse_building_lod1(building)
            if mesh is not None:
                meshes.append(mesh)

        return meshes

    except ET.ParseError:
        logger.exception(f"XMLパースエラー: {gml_file}")
        return []
    except Exception:
        logger.exception(f"予期しないエラー: {gml_file}")
        return []


def load_buildings_from_directory(
    gml_dir: Path, max_files: int | None = None
) -> pv.PolyData:
    """
    ディレクトリ内の全CityGMLファイルをパースして結合.

    Parameters
    ----------
    gml_dir : Path
        CityGMLファイルが格納されたディレクトリ
    max_files : int | None
        処理する最大ファイル数（None=全て）

    Returns
    -------
    pv.PolyData
        結合された建物メッシュ

    """
    gml_files = sorted(gml_dir.glob("*.gml"))
    logger.info(f"{len(gml_files)}個のGMLファイルを検出")

    if max_files is not None:
        gml_files = gml_files[:max_files]
        logger.info(f"最初の{max_files}ファイルのみ処理します")

    all_meshes = []
    for i, gml_file in enumerate(gml_files, 1):
        logger.info(f"  [{i}/{len(gml_files)}] {gml_file.name} を処理中...")
        meshes = parse_citygml_file(gml_file)
        all_meshes.extend(meshes)

    if not all_meshes:
        logger.warning("メッシュが生成されませんでした")
        return pv.PolyData()

    logger.info(f"合計 {len(all_meshes)}棟の建物メッシュを生成")

    # 全メッシュを結合
    logger.info("メッシュを結合中...")
    combined = all_meshes[0]
    for mesh in all_meshes[1:]:
        combined = combined.merge(mesh)

    logger.info(f"結合完了: {combined.n_points}点, {combined.n_cells}面")

    return combined


def visualize_buildings(
    buildings: pv.PolyData,
    screenshot_path: Path | None = None,
    terrain: pv.StructuredGrid | None = None,
) -> None:
    """
    建物メッシュと地形をPyVistaで可視化.

    Parameters
    ----------
    buildings : pv.PolyData
        建物メッシュ
    screenshot_path : Path | None
        スクリーンショット保存先（Noneの場合はインタラクティブ表示）
    terrain : pv.StructuredGrid | None
        地形データ（オプション）

    """
    logger.info("PyVistaで可視化中...")

    # オフスクリーンモード判定
    off_screen = screenshot_path is not None

    plotter = pv.Plotter(
        off_screen=off_screen, window_size=[1920, 1080] if off_screen else None
    )

    # 地形を追加（オプション）
    fuji_point = None
    if terrain is not None:
        logger.info("地形データを追加...")
        # 地形は茶色系で表示（富士山を強調）
        plotter.add_mesh(
            terrain,
            cmap="gist_earth",  # 茶色〜緑の地形カラーマップ
            opacity=0.8,
            show_edges=False,
            show_scalar_bar=True,
            clim=[0, 4000],  # カラースケールを0-4000mに設定
        )

        # 富士山の位置にマーカーを追加
        # 地形の最大標高点を探す
        max_z_idx = np.argmax(terrain.points[:, 2])
        fuji_point = terrain.points[max_z_idx]
        logger.info(
            f"富士山の位置: X={fuji_point[0]:.0f}, Y={fuji_point[1]:.0f}, Z={fuji_point[2]:.0f}m"
        )

        # 富士山にラベルを追加
        plotter.add_point_labels(
            [fuji_point],
            ["富士山"],
            point_size=40,
            font_size=48,
            text_color="white",
            point_color="red",
            bold=True,
            shadow=True,
        )

    # 建物を追加（青灰色で表示、地形と差別化）
    plotter.add_mesh(
        buildings,
        color="steelblue",  # 青灰色
        show_edges=True,
        edge_color="navy",
        line_width=0.3,
        opacity=1.0,
    )

    # カメラ設定
    if terrain is not None and fuji_point is not None:
        # ソラシティ21階から富士山を望む視点
        # 建物の高さを10倍に誇張しているので、カメラの高さも調整
        solacity_pos = np.array([3566615.0, 13972468.0, 700.0])  # 21階×10 = 約700m

        # カメラを建物の中（低い位置）に配置して、建物の間から富士山を見上げる構図
        camera_offset = np.array([-500.0, 500.0, -200.0])  # 低めの位置
        camera_pos = solacity_pos + camera_offset

        plotter.camera_position = [
            camera_pos.tolist(),  # カメラ位置
            fuji_point.tolist(),  # 富士山を注視
            (0, 0, 1),  # 上方向
        ]

        # 視野角をさらに狭めて望遠レンズのように
        plotter.camera.view_angle = 20.0  # より望遠

        # クリッピング範囲を設定（手前の建物から遠くの富士山まで）
        plotter.camera.clipping_range = (50, 200000)

        logger.info("カメラ視点: 建物の間から富士山を見上げる（望遠レンズ）")
        logger.info(
            f"  カメラ位置: X={camera_pos[0]:.0f}, Y={camera_pos[1]:.0f}, Z={camera_pos[2]:.0f}m"
        )
        logger.info(
            f"  注視点: 富士山 (約{np.linalg.norm(fuji_point - solacity_pos) / 1000:.0f}km先)"
        )
        logger.info(f"  視野角: 20度（望遠レンズ）、クリッピング範囲: 50m〜200km")
    elif terrain is not None:
        # 地形がある場合は広域表示
        center = terrain.center
        plotter.camera_position = [
            (center[0] - 30000, center[1] - 30000, 10000),
            center,
            (0, 0, 1),
        ]
    else:
        # 建物のみの場合
        center = buildings.center
        plotter.camera_position = [
            (center[0] - 1500, center[1] - 1500, 500),
            center,
            (0, 0, 1),
        ]

    plotter.add_axes()

    if screenshot_path:
        # スクリーンショット保存
        logger.info(f"スクリーンショット保存中: {screenshot_path}")
        plotter.screenshot(str(screenshot_path))
        logger.info("✓ 画像を保存しました")
    else:
        # インタラクティブ表示
        logger.info("✓ 可視化ウィンドウを表示します")
        logger.info("  - マウスドラッグ: 回転")
        logger.info("  - ホイール: ズーム")
        logger.info("  - q: 終了")
        plotter.show()


def main() -> None:
    """メインエントリーポイント."""
    parser = argparse.ArgumentParser(
        prog="python -m src.visualizer",
        description="PLATEAU 3D都市モデルの可視化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("data/plateau/udx/bldg"),
        help="CityGMLファイルのディレクトリ (デフォルト: data/plateau/udx/bldg)",
    )
    parser.add_argument(
        "-n",
        "--max-files",
        type=int,
        help="処理する最大ファイル数（テスト用）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="メッシュをファイルに保存する場合のパス (.vtp形式)",
    )
    parser.add_argument(
        "-t",
        "--terrain",
        type=Path,
        help="地形データファイル (.vts形式)",
    )
    parser.add_argument(
        "-s",
        "--screenshot",
        type=Path,
        help="スクリーンショットを保存する場合のパス (.png形式)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細な出力")

    args = parser.parse_args()

    # ログレベルの設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("=== PLATEAU 3D都市モデル可視化 ===")
    logger.info(f"入力ディレクトリ: {args.input}")

    # ディレクトリの存在確認
    if not args.input.exists():
        logger.error(f"ディレクトリが存在しません: {args.input}")
        logger.info("先に以下のコマンドでPLATEAUデータをダウンロードしてください:")
        logger.info("  python -m src.downloader -o data/plateau --verbose")
        return

    # CityGMLファイルのロードと変換
    logger.info("CityGMLファイルをロード中...")
    buildings = load_buildings_from_directory(args.input, args.max_files)

    if buildings.n_points == 0:
        logger.error("建物データが読み込めませんでした")
        return

    # 地面にZ座標を正規化
    logger.info("建物を地面に配置...")
    bounds = buildings.bounds
    z_min = bounds[4]
    buildings.translate([0, 0, -z_min], inplace=True)
    logger.info(f"  Z座標オフセット: {-z_min:.2f}m")

    # 座標スケーリング（緯度経度→メートル相当）
    logger.info("座標をスケーリング中...")
    points = buildings.points.copy()
    points[:, 0] *= 100000  # X (緯度) を100,000倍
    points[:, 1] *= 100000  # Y (経度) を100,000倍
    # Z（高さ）を10倍に誇張して、建物が見やすくする
    height_exaggeration = 10.0
    points[:, 2] *= height_exaggeration
    buildings.points = points
    logger.info(
        f"  スケーリング後の範囲: "
        f"X={buildings.bounds[0]:.0f}〜{buildings.bounds[1]:.0f}m, "
        f"Y={buildings.bounds[2]:.0f}〜{buildings.bounds[3]:.0f}m, "
        f"Z={buildings.bounds[4]:.1f}〜{buildings.bounds[5]:.1f}m (高さ{height_exaggeration}倍誇張)"
    )

    # メッシュを保存（オプション）
    if args.output:
        logger.info(f"メッシュを保存中: {args.output}")
        buildings.save(args.output)
        logger.info("✓ 保存完了")

    # 地形データを読み込み（オプション）
    terrain = None
    if args.terrain:
        if args.terrain.exists():
            logger.info(f"地形データを読み込み中: {args.terrain}")
            terrain = pv.read(args.terrain)
            logger.info(f"  地形範囲: Z={terrain.bounds[4]:.0f}〜{terrain.bounds[5]:.0f}m")
        else:
            logger.warning(f"地形データが見つかりません: {args.terrain}")
            logger.info("先に以下のコマンドでDEMデータを生成してください:")
            logger.info("  uv run python -c 'from src.downloader.dem import download_dem; download_dem()'")

    # PyVistaで可視化
    visualize_buildings(buildings, args.screenshot, terrain)


if __name__ == "__main__":
    main()
