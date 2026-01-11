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
        # 地形はterrainカラーマップで標高を色分け
        plotter.add_mesh(
            terrain,
            scalars=terrain.points[:, 2],  # Z座標（標高）をスカラー値として使用
            cmap="terrain",  # terrainカラーマップ（青→緑→黄→茶）
            opacity=0.8,
            show_edges=False,
            show_scalar_bar=True,
            clim=[0, 4000],  # カラースケールを0-4000mに設定
        )

        # 富士山の位置を検出（マーカーは表示しない）
        max_z_idx = np.argmax(terrain.points[:, 2])
        fuji_point = terrain.points[max_z_idx]
        logger.info(
            f"富士山の位置: X={fuji_point[0]:.0f}, Y={fuji_point[1]:.0f}, Z={fuji_point[2]:.0f}m"
        )

    # 建物を追加（黄色で表示、地形と明確に差別化）
    plotter.add_mesh(
        buildings,
        color="yellow",  # 明るい黄色
        show_edges=False,
        opacity=1.0,
    )

    # カメラ設定
    if terrain is not None and fuji_point is not None:
        # 建物と富士山の両方が見える視点を設定
        solacity_pos = np.array([3566615.0, 13972468.0, 700.0])  # ソラシティ位置

        # 建物と富士山の中心をnumpy配列で取得
        fuji_center = np.array(terrain.center)
        bldg_center = np.array(buildings.center)

        # 富士山と建物の距離を計算
        distance = np.linalg.norm(fuji_center - bldg_center)
        logger.info(f"富士山と建物の距離: {distance / 1000:.1f}km")

        # 建物の背後（北東側）からカメラを配置
        # 建物が手前、富士山が奥に見える構図
        camera_pos = bldg_center + np.array([15000, 15000, 5000])

        # 中間点を注視
        focal_point = (fuji_center + bldg_center) / 2

        plotter.camera_position = [
            camera_pos.tolist(),
            focal_point.tolist(),
            (0, 0, 1),
        ]

        # 視野角
        plotter.camera.view_angle = 50.0

        # クリッピング範囲
        plotter.camera.clipping_range = (100, 200000)

        logger.info("カメラ視点: 建物の背後から富士山方向を見る")
        logger.info(
            f"  カメラ位置: X={camera_pos[0]:.0f}, Y={camera_pos[1]:.0f}, Z={camera_pos[2]:.0f}m"
        )
        logger.info(f"  注視点(中間): X={focal_point[0]:.0f}, Y={focal_point[1]:.0f}, Z={focal_point[2]:.0f}m")
        logger.info(f"  視野角: 50度、クリッピング範囲: 100m〜200km")
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
    # Z（高さ）を30倍に誇張して、建物が見やすくする
    height_exaggeration = 30.0
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
