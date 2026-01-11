"""
PLATEAUデータのダウンロード.

千代田区の建物データをG空間情報センターのCKAN APIから取得します。
"""

import logging
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

# G空間情報センター CKAN API
CKAN_API_BASE = "https://www.geospatial.jp/ckan/api/3/action"


def get_dataset_resources(dataset_id: str) -> list[dict]:
    """
    CKANデータセットからリソース情報を取得.

    Parameters
    ----------
    dataset_id : str
        データセットID (例: 'plateau-13101-chiyoda-ku-2023')

    Returns
    -------
    List[Dict]
        リソースのリスト
    """
    url = f"{CKAN_API_BASE}/package_show"
    params = {"id": dataset_id}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data["result"]["resources"]
        logger.error(f"CKAN API エラー: {data.get('error', 'Unknown error')}")
        return []

    except Exception:
        logger.exception("データセット情報の取得に失敗")
        return []


def find_citygml_resource(resources: list[dict]) -> dict | None:
    """
    CityGML形式の建物データリソースを検索.

    Parameters
    ----------
    resources : List[Dict]
        リソースのリスト

    Returns
    -------
    Optional[Dict]
        見つかったリソース、見つからない場合はNone
    """
    # まずZIP形式のリソースのみをフィルタ
    zip_resources = [r for r in resources if r.get("format", "").lower() == "zip"]

    logger.debug(f"ZIP形式のリソース数: {len(zip_resources)}")
    for i, r in enumerate(zip_resources, 1):
        name = r.get("name", "N/A")
        desc = r.get("description", "N/A")[:50]
        logger.debug(f"  {i}. name='{name}', desc='{desc}'")

    # 優先順位付きのキーワード検索
    # 具体的なファイル名パターンから順に検索し、最適なリソースを見つける
    priority_patterns = [
        ["bldg", "citygml", "lod2"],  # 建物、CityGML、LOD2
        ["bldg", "citygml", "lod1"],  # 建物、CityGML、LOD1
        ["bldg", "citygml"],  # 建物、CityGML
        ["citygml"],  # CityGML単体マッチ
    ]

    for pattern in priority_patterns:
        logger.debug(f"パターン検索: {pattern}")
        for resource in zip_resources:
            name = resource.get("name", "").lower()
            description = resource.get("description", "").lower()

            # 除外キーワード（建物以外のデータ）
            exclude_keywords = [
                "3d tiles",
                "mvt",
                "terrain",
                "dem",
                "texture",
                "関連データセット",
                "索引図",
            ]
            if any(ex in name for ex in exclude_keywords):
                logger.debug(f"  除外: {name} (除外キーワードマッチ)")
                continue

            # パターンマッチ
            if all(kw in name or kw in description for kw in pattern):
                logger.info(f"✓ マッチしたリソース: {name}")
                return resource

    # フォールバック: "CityGML"という名前のZIPファイル
    logger.debug("フォールバック検索")
    for resource in zip_resources:
        name = resource.get("name", "").lower()
        logger.debug(f"  チェック: {name}")
        if "citygml" in name and "(" in name:  # 「CityGML（v4）」のようなパターン
            logger.info(f"✓ フォールバックでマッチ: {name}")
            return resource

    return None


def download_plateau(
    output_dir: str = "data/plateau/ochanomizu",
    bbox: tuple | None = None,
    verbose: bool = True,
    dataset_id: str = "plateau-13101-chiyoda-ku-2023",
) -> Path:
    """
    PLATEAUの建物データをG空間情報センターCKAN APIからダウンロード.

    Parameters
    ----------
    output_dir : str
        出力ディレクトリパス
    bbox : tuple, optional
        (min_lon, min_lat, max_lon, max_lat) の範囲指定
        デフォルトは御茶ノ水ソラシティ周辺 半径1km
    verbose : bool
        進行状況を表示するかどうか
    dataset_id : str
        PLATEAUデータセットID（デフォルト: 千代田区2023年度）

    Returns
    -------
    Path
        ダウンロードしたデータのディレクトリパス
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # bboxが指定されていない場合、御茶ノ水ソラシティ周辺をデフォルトとする
    if bbox is None:
        lat, lon = 35.6996, 139.7645
        delta = 0.01  # 約1km
        bbox = (lon - delta, lat - delta, lon + delta, lat + delta)

    logger.info("PLATEAUデータをダウンロード中...")
    logger.info(f"  データセット: {dataset_id}")
    logger.info(f"  範囲: {bbox}")
    logger.info(f"  出力先: {out_dir}")

    # CKAN APIからデータセット情報を取得
    logger.info("G空間情報センターCKAN APIに接続中...")
    resources = get_dataset_resources(dataset_id)

    if not resources:
        logger.error("データセット情報の取得に失敗しました")
        _show_manual_download_instructions(out_dir, dataset_id)
        return out_dir

    logger.info(f"リソース数: {len(resources)}")

    # CityGML建物データを検索
    resource = find_citygml_resource(resources)

    if not resource:
        logger.error("CityGML形式の建物データが見つかりませんでした")
        logger.info(f"利用可能なリソース: {len(resources)}件")
        for i, r in enumerate(resources[:5], 1):  # 最初の5件を表示
            logger.info(f"  {i}. {r.get('name', 'N/A')} ({r.get('format', 'N/A')})")
        _show_manual_download_instructions(out_dir, dataset_id)
        return out_dir

    # ダウンロードURL取得
    download_url = resource.get("url")
    resource_name = resource.get("name", "plateau_data")

    logger.info(f"ダウンロード対象: {resource_name}")
    logger.info(f"形式: {resource.get('format', 'N/A')}")
    logger.info(f"サイズ: {resource.get('size', 'N/A')}")

    if not download_url:
        logger.error("ダウンロードURLが見つかりませんでした")
        _show_manual_download_instructions(out_dir, dataset_id)
        return out_dir

    # ダウンロード実行
    zip_path = out_dir / "plateau_data.zip"

    try:
        logger.info(f"ダウンロード開始: {download_url}")
        response = requests.get(download_url, stream=True, timeout=120)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with zip_path.open("wb") as f:
            if verbose and total_size > 0:
                with tqdm(
                    total=total_size, unit="B", unit_scale=True, desc="ダウンロード中"
                ) as pbar:
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
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(out_dir)

        logger.info(f"展開完了: {out_dir}")

        # ZIPファイルを削除
        if zip_path.exists():
            zip_path.unlink()
            logger.debug(f"ZIPファイルを削除: {zip_path}")

        logger.info("✓ PLATEAUデータのダウンロードが完了しました")

    except requests.exceptions.RequestException:
        logger.exception("ダウンロードエラー")
        if zip_path.exists():
            zip_path.unlink()
        _show_manual_download_instructions(out_dir, dataset_id)
    except zipfile.BadZipFile:
        logger.exception("ZIPファイルの展開エラー")
        if zip_path.exists():
            zip_path.unlink()
        _show_manual_download_instructions(out_dir, dataset_id)
    except Exception:
        logger.exception("予期しないエラー")
        if zip_path.exists():
            zip_path.unlink()
        raise

    return out_dir


def _show_manual_download_instructions(out_dir: Path, dataset_id: str) -> None:
    """手動ダウンロード手順を表示."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("=== PLATEAUデータ 手動ダウンロード手順 ===")
    logger.info("=" * 60)
    logger.info("")
    logger.info("1. 以下のURLをブラウザで開いてください:")
    logger.info(f"   https://www.geospatial.jp/ckan/dataset/{dataset_id}")
    logger.info("")
    logger.info("2. ページ内の「3D都市モデル（建築物モデル）」セクションを探し、")
    logger.info("   CityGML形式のZIPファイル（LOD2推奨）をダウンロードしてください。")
    logger.info("")
    logger.info("3. ダウンロードしたZIPファイルを以下のディレクトリに展開:")
    logger.info(f"   {out_dir.absolute()}")
    logger.info("")
    logger.info("=" * 60)
    logger.info("")
