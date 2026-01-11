"""
DEMデータのダウンロード.

国土地理院の基盤地図情報から標高データを取得します。
"""

import logging
from pathlib import Path

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
        logger.info("DEMデータをダウンロード中...")
        logger.info(f"  地域: {region}")
        logger.info(f"  出力先: {out_dir}")

    # TODO: 国土地理院APIを使用した実装
    # 現在はスタブ実装
    logger.warning("[スタブ] DEMデータのダウンロードは未実装です")

    if verbose:
        logger.info("国土地理院の基盤地図情報から手動でダウンロードしてください")
        logger.info("参考: https://fgd.gsi.go.jp/")

    return out_dir
