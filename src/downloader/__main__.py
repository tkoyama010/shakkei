"""
ダウンローダーモジュールのCLIエントリーポイント

使用方法:
    python -m src.downloader
"""

import argparse
import logging

from .plateau import download_plateau


logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        prog="python -m src.downloader",
        description="PLATEAUとDEMデータをダウンロード",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-o", "--output",
        default="data/plateau/ochanomizu",
        help="出力ディレクトリ"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細な出力"
    )

    args = parser.parse_args()

    # ログレベルの設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("ダウンローダーモジュールを実行")

    # PLATEAUデータのダウンロード
    try:
        download_plateau(output_dir=args.output, verbose=args.verbose)
    except Exception as e:
        logger.error(f"ダウンロードに失敗しました: {e}")
        raise


if __name__ == "__main__":
    main()
