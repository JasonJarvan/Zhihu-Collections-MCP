import main as main_module

config = main_module.load_config()
main_module.base_output_path = str(
    main_module.parse_output_path(config["outputPath"], config.get("os", ""))
)

for c in config["zhihuUrls"]:
    print(f"========== {c['name']} ==========")
    main_module.process_single_collection(c["name"], c["url"])

print("ALL DONE")
