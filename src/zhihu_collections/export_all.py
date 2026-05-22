from zhihu_collections import main as main_module


def main():
    config = main_module.load_config()
    base_output_path = None
    if config.get("outputPath"):
        base_output_path = str(
            main_module.parse_output_path(config["outputPath"], config.get("os", ""))
        )

    context = main_module.ExportContext(
        base_output_path=base_output_path,
        headers=main_module._build_page_headers(),
        api_headers=main_module._build_api_headers(),
        cookies=main_module.load_cookies(),
        markdown_format=config.get("markdownFormat", "obsidian"),
    )

    for c in config["zhihuUrls"]:
        print(f"========== {c['name']} ==========")
        main_module.process_single_collection(c["name"], c["url"], context)

    print("ALL DONE")


if __name__ == "__main__":
    main()
