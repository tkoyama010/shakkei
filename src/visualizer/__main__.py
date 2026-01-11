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


def visualize_buildings(buildings: pv.PolyData) -> None:
    """
    建物メッシュをPyVistaで可視化.

    Parameters
    ----------
    buildings : pv.PolyData
        建物メッシュ

    """
    logger.info("PyVistaで可視化中...")
    plotter = pv.Plotter()
    plotter.add_mesh(
        buildings,
        color="lightgray",
        show_edges=False,
        smooth_shading=True,
        specular=0.2,
    )

    # カメラ設定
    plotter.camera_position = "xy"
    plotter.add_axes()
    plotter.show_grid()

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

    # メッシュを保存（オプション）
    if args.output:
        logger.info(f"メッシュを保存中: {args.output}")
        buildings.save(args.output)
        logger.info("✓ 保存完了")

    # PyVistaで可視化
    visualize_buildings(buildings)


if __name__ == "__main__":
    main()
