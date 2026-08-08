from zhihu_collections._common import load_config, load_cookies, parse_output_path
from zhihu_collections._logging import setup_debug_logging, reconfigure_logging
from zhihu_collections._paths import get_output_path, get_logs_path, get_debug_path
from zhihu_collections._headers import build_page_headers, build_api_headers
from zhihu_collections._export import ExportContext, create_export_context, save_processing_log, is_article_already_downloaded, get_unique_filename
from zhihu_collections._collection import process_single_collection, get_article_urls_in_collection, get_article_nums_of_collection, remove_articles_from_collection
from zhihu_collections._converter import markdownify
from zhihu_collections._operations import (
    list_collections,
    export_single_collection,
    get_collection_info,
    search_collections,
    add_article_to_collection,
    remove_article_from_collection,
    move_article_between_collections,
    resolve_output_path,
)
from zhihu_collections.utils import filter_title_str
from zhihu_collections import favorite_ops


def export_main():
    from zhihu_collections.main import main
    main()
