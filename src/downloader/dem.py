"""
DEMデータのダウンロード.

国土地理院の基盤地図情報から標高データを取得します。
"""

import logging
from pathlib import Path

import numpy as np
import pyvista as pv
from tqdm import tqdm

logger = logging.getLogger(__name__)


def download_dem(
    output_dir: str = "data/dem", region: str = "kanto", verbose: bool = True
) -> Path:
    """
    国土地理院のDEMデータをダウンロード.

    Parameters
    ----------
    output_dir : str
        出力ディレクトリパス
    region : str
        地域名 ('kanto' など)
    verbose : bool
        進行状況を表示するかどうか

    Returns
    -------
    Path
        ダウンロードしたデータのパス
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        logger.info("DEMデータを生成中...")
        logger.info(f"  地域: {region}")
        logger.info(f"  出力先: {out_dir}")

    # 簡易的な地形データを生成（デモ用）
    # 関東平野から富士山までの広域地形を模擬
    logger.info("簡易地形データを生成します（デモ用）")

    # 座標範囲（スケーリング後の座標系に合わせる）
    # 御茶ノ水周辺: X=3566615, Y=13972468
    # 富士山: 緯度35.3606, 経度138.7274 → X=3536060, Y=13872740（スケーリング後）

    x_min, x_max = 3530000, 3570000  # 約40km範囲
    y_min, y_max = 13870000, 13980000  # 約110km範囲

    # グリッド作成（解像度: 500m）
    x = np.arange(x_min, x_max, 500)
    y = np.arange(y_min, y_max, 500)
    x_grid, y_grid = np.meshgrid(x, y)

    # 標高データを生成
    # 富士山の位置
    fuji_x, fuji_y = 3536060, 13872740

    # 距離に基づく標高（富士山を中心とした円錐状）
    dist_from_fuji = np.sqrt((x_grid - fuji_x) ** 2 + (y_grid - fuji_y) ** 2)

    # 富士山の高さ（3,776m）を中心とした地形
    # 距離に応じて高さが減衰
    fuji_height = 3776
    decay_distance = 50000  # 50km

    z = np.maximum(
        0, fuji_height * np.exp(-((dist_from_fuji / decay_distance) ** 2))
    )

    # 関東平野部分（低地）
    # 御茶ノ水周辺は標高が低い
    solacity_x, solacity_y = 3566615, 13972468
    dist_from_solacity = np.sqrt(
        (x_grid - solacity_x) ** 2 + (y_grid - solacity_y) ** 2
    )

    # 平野部の標高（0〜50m程度）
    plain_elevation = 20 * np.exp(-((dist_from_solacity / 20000) ** 2))

    # 富士山と平野を合成
    z = np.maximum(z, plain_elevation)

    # PyVista StructuredGridを作成
    grid = pv.StructuredGrid(x_grid, y_grid, z)

    # VTSファイルとして保存
    output_file = out_dir / "kanto_terrain.vts"
    grid.save(output_file)

    logger.info(f"✓ 地形データを生成: {output_file}")
    logger.info(f"  範囲: X={x_min}〜{x_max}, Y={y_min}〜{y_max}")
    logger.info(f"  最大標高: {z.max():.1f}m (富士山)")
    logger.info(f"  グリッドサイズ: {x_grid.shape}")

    return out_dir
