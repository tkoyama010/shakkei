"""
PLATEAUデータのダウンロード

千代田区の建物データをPLATEAU APIから取得します。
"""

import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def download_plateau(
    output_dir: str = "data/plateau/ochanomizu",
    bbox: Optional[tuple] = None,
    verbose: bool = True
) -> Path:
    """
    PLATEAUの建物データをダウンロード

    Parameters
    ----------
    output_dir : str
        出力ディレクトリパス
    bbox : tuple, optional
        (min_lon, min_lat, max_lon, max_lat) の範囲指定
        デフォルトは御茶ノ水ソラシティ周辺 半径1km
    verbose : bool
        進行状況を表示するかどうか

    Returns
    -------
    Path
        ダウンロードしたデータのディレクトリパス
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # デフォルトbbox: 御茶ノ水ソラシティ周辺
    if bbox is None:
        lat, lon = 35.6996, 139.7645
        delta = 0.01  # 約1km
        bbox = (lon - delta, lat - delta, lon + delta, lat + delta)

    logger.info(f"PLATEAUデータをダウンロード中...")
    logger.info(f"  範囲: {bbox}")
    logger.info(f"  出力先: {out_dir}")

    # TODO: plateaupy APIを使用した実装
    # 現在はスタブ実装
    logger.warning("[スタブ] PLATEAUデータのダウンロードは未実装です")
    logger.info("plateaupy APIまたは手動ダウンロードを使用してください")
    logger.info(f"参考: https://www.mlit.go.jp/plateau/")

    return out_dir
