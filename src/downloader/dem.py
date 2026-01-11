"""
DEMデータのダウンロード.

国土地理院の基盤地図情報から標高データを取得します。
GeoVistaとrasterioを使用してGeoTIFFファイルを処理します。
"""

import logging
from pathlib import Path

import numpy as np
import pyvista as pv
import rasterio
from pyproj import Transformer

logger = logging.getLogger(__name__)


def load_geotiff_with_rasterio(
    tiff_path: Path, target_epsg: int = 6677, scale_factor: float = 1.0
) -> pv.StructuredGrid:
    """
    rasterioでGeoTIFFファイルからDEMデータを読み込み.

    Parameters
    ----------
    tiff_path : Path
        GeoTIFFファイルのパス
    target_epsg : int
        変換先の座標系EPSG コード（デフォルト: 6677 = 平面直角座標系IX）
    scale_factor : float
        標高のスケーリング係数（誇張表現用、デフォルト1.0）

    Returns
    -------
    pv.StructuredGrid
        地形メッシュ

    """
    logger.info(f"GeoTIFFファイルを読み込み中: {tiff_path}")

    with rasterio.open(tiff_path) as src:
        # 標高データを読み込み
        elevation = src.read(1)

        # nodata値を除外
        nodata = src.nodata
        if nodata is not None:
            elevation = np.where(elevation == nodata, 0, elevation)
            logger.info(f"  nodata値({nodata})を0に置換")

        logger.info(f"  解像度: {elevation.shape}")
        logger.info(f"  標高範囲: {elevation.min():.1f}〜{elevation.max():.1f}m")

        # 元の座標系
        src_crs = src.crs
        logger.info(f"  元の座標系: {src_crs}")

        # グリッドの座標を生成
        rows, cols = elevation.shape
        lon_coords = np.zeros((rows, cols))  # 経度
        lat_coords = np.zeros((rows, cols))  # 緯度

        for row in range(rows):
            for col in range(cols):
                lon, lat = src.xy(row, col)  # src.xy()は(lon, lat)を返す
                lon_coords[row, col] = lon
                lat_coords[row, col] = lat

        logger.info(
            f"  元の座標範囲: 経度={lon_coords.min():.1f}〜{lon_coords.max():.1f}, "
            f"緯度={lat_coords.min():.1f}〜{lat_coords.max():.1f}"
        )

        # 緯度経度を100,000倍してメートル相当に変換
        # PyVistaでの表示用の座標系（X=緯度×100000, Y=経度×100000）
        x_coords = lat_coords * 100000  # X = 緯度
        y_coords = lon_coords * 100000  # Y = 経度

        logger.info("  緯度経度を100,000倍してメートル相当に変換")

        # 標高を誇張（オプション）
        z_coords = elevation * scale_factor

        logger.info(
            f"  最終座標範囲: X={x_coords.min():.0f}〜{x_coords.max():.0f}, "
            f"Y={y_coords.min():.0f}〜{y_coords.max():.0f}, "
            f"Z={z_coords.min():.1f}〜{z_coords.max():.1f}m"
        )

    # PyVista StructuredGridを作成
    grid = pv.StructuredGrid(x_coords, y_coords, z_coords)

    return grid


def download_dem_from_geovista_pantry(
    output_dir: str = "data/dem", verbose: bool = True, scale_factor: float = 1.0
) -> Path:
    """
    GeoVistaのサンプルDEMデータ（富士山）をダウンロード.

    Parameters
    ----------
    output_dir : str
        出力ディレクトリパス
    verbose : bool
        進行状況を表示するかどうか
    scale_factor : float
        標高の誇張係数（デフォルト1.0）

    Returns
    -------
    Path
        ダウンロードしたデータのパス

    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        logger.info("GeoVistaサンプルDEM（富士山）をダウンロード中...")

    # GeoVistaのサンプルデータを取得
    from geovista.pantry import fetch_raster

    tiff_path = fetch_raster("fuji_dem.tif")
    logger.info(f"✓ サンプルDEMを取得: {tiff_path}")

    # rasterioでGeoTIFFを読み込み
    mesh = load_geotiff_with_rasterio(
        Path(tiff_path), target_epsg=6677, scale_factor=scale_factor
    )

    # VTSファイルとして保存
    output_file = out_dir / "fuji_dem.vts"
    mesh.save(output_file)

    logger.info(f"✓ 地形データを保存: {output_file}")

    return out_dir


def download_dem(
    output_dir: str = "data/dem",
    region: str = "kanto",
    verbose: bool = True,
    use_sample: bool = True,
) -> Path:
    """
    DEMデータをダウンロード.

    Parameters
    ----------
    output_dir : str
        出力ディレクトリパス
    region : str
        地域名 ('kanto' など)
    verbose : bool
        進行状況を表示するかどうか
    use_sample : bool
        GeoVistaのサンプルデータを使用するか

    Returns
    -------
    Path
        ダウンロードしたデータのパス

    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if use_sample:
        # GeoVistaのサンプルDEM（富士山）を使用
        return download_dem_from_geovista_pantry(output_dir, verbose)

    # 以下は将来の実装用（国土地理院の実データ）
    if verbose:
        logger.info("国土地理院DEMデータのダウンロード...")
        logger.info(f"  地域: {region}")
        logger.info(f"  出力先: {out_dir}")

    logger.warning("国土地理院DEMの自動ダウンロードは未実装です")
    logger.info("")
    logger.info("=== 国土地理院DEMデータ 手動ダウンロード手順 ===")
    logger.info("1. 以下のURLにアクセス:")
    logger.info("   https://fgd.gsi.go.jp/")
    logger.info("2. 「基盤地図情報 数値標高モデル」をダウンロード")
    logger.info("3. GeoTIFF形式でエクスポート")
    logger.info(f"4. {out_dir}/terrain.tif として保存")
    logger.info("5. 以下のコマンドで読み込み:")
    logger.info(
        "   from src.downloader.dem import load_geotiff_with_rasterio; "
        f"load_geotiff_with_rasterio(Path('{out_dir}/terrain.tif'))"
    )
    logger.info("")

    return out_dir
