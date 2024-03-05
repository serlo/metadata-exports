def enhance_metadata(metadata_file, enhanced_metadata_path):
    DESCRIPTION_PATH = "public/description-cache.json"

    with open(metadata_file, "r", encoding="utf-8") as input_file:
        resources = json.load(input_file)

    with open(DESCRIPTION_PATH, "r", encoding="utf-8") as input_file:
        description_cache = json.load(input_file)

    enhanced_resources = map(lambda x: enhance(x, description_cache), resources)


    #TODO: time and update description cache


    with open(enhanced_metadata_path, "w", encoding="utf-8") as output_file:
        json.dump(enhanced_resources, output_file)

    return


def enhance(resource, description_cache):
    if "description" in resource and isinstance(resource["description"], str):
        return resource

    cached_value = description_cache.get(resource["id"], {})

    if cached_value.get("version", None) == resource["version"] and isinstance(
            cached_value.get("description", None), str
    ):
        resource["description"] = cached_value["description"]
        return resource

    new_description = load_description_from_website(resource)

    description_cache[resource["id"]] = {
        "description": new_description,
        "version": resource["version"],
    }

    resource["description"] = description_cache[resource["id"]]

    return resource