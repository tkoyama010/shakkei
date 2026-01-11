"""
PLATEAUデータのダウンロード

千代田区の建物データをPLATEAU APIから取得します。
"""

import logging
import zipfile
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm


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

    # 千代田区のPLATEAU 3D都市モデルデータ（2023年度）
    # G空間情報センターのCKANポータルから取得
    # 複数のURL候補を試す
    urls = [
        # 2023年度データ (CityGML 3.0)
        "https://assets.cms.plateau.reearth.io/assets/2c/4e45a4-e2dd-4421-bec3-4eb3aa5ba6e5/13101_chiyoda-ku_2023_citygml_3_op.zip",
        # 2023年度データ (CityGML 2.0互換)
        "https://assets.cms.plateau.reearth.io/assets/b7/7c7cfa-5e95-4a38-9b59-02e5a4fde89f/13101_chiyoda-ku_2023_citygml_2_op.zip",
    ]

    zip_path = out_dir / "plateau_chiyoda.zip"
    success = False

    for url in urls:
        try:
            # ダウンロード
            logger.info(f"ダウンロード試行中: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(zip_path, 'wb') as f:
                if verbose and total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="ダウンロード中") as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            logger.info(f"ダウンロード完了: {zip_path}")

            # ZIPファイルの展開
            logger.info("ZIPファイルを展開中...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(out_dir)

            logger.info(f"展開完了: {out_dir}")

            # ZIPファイルを削除（オプション）
            if zip_path.exists():
                zip_path.unlink()
                logger.debug(f"ZIPファイルを削除: {zip_path}")

            logger.info("PLATEAUデータのダウンロードが完了しました")
            success = True
            break

        except requests.exceptions.RequestException as e:
            logger.warning(f"URLからのダウンロード失敗: {url}")
            logger.debug(f"エラー詳細: {e}")
            continue
        except zipfile.BadZipFile as e:
            logger.error(f"ZIPファイルの展開エラー: {e}")
            if zip_path.exists():
                zip_path.unlink()
            continue

    if not success:
        logger.warning("自動ダウンロードに失敗しました。手動ダウンロードが必要です。")
        logger.info("")
        logger.info("=" * 60)
        logger.info("=== PLATEAUデータ 手動ダウンロード手順 ===")
        logger.info("=" * 60)
        logger.info("")
        logger.info("1. 以下のURLをブラウザで開いてください:")
        logger.info("   https://www.geospatial.jp/ckan/dataset/plateau-13101-chiyoda-ku-2023")
        logger.info("")
        logger.info("2. ページ内の「3D都市モデル（建築物モデル）」セクションを探し、")
        logger.info("   CityGML形式のZIPファイル（LOD2推奨）をダウンロードしてください。")
        logger.info("")
        logger.info("3. ダウンロードしたZIPファイルを以下のディレクトリに展開:")
        logger.info(f"   {out_dir.absolute()}")
        logger.info("")
        logger.info("4. 展開後、以下のようなフォルダ構造になっていることを確認:")
        logger.info(f"   {out_dir.absolute()}/")
        logger.info("   └── udx/")
        logger.info("       └── bldg/")
        logger.info("           └── *.gml (CityGMLファイル)")
        logger.info("")
        logger.info("=" * 60)
        logger.info("")
        logger.info("注: PLATEAUデータは認証が必要な場合や、ブラウザでの操作が")
        logger.info("    必要な場合があるため、自動ダウンロードができません。")
        logger.info("")

    return out_dir
