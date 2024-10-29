import json
import fastjsonschema
from pathlib import PurePath
import requests
import time

with open(
    f"{str(PurePath(__file__).parent)}/public/serlo-metadata.json",
    "r",
    encoding="utf-8",
) as serlo_metadata_file:
    serlo_metadata_plain = serlo_metadata_file.read()
    learning_resources = json.loads(serlo_metadata_plain)

schema = requests.get(
    "https://w3id.org/kim/amb/draft/schemas/schema.json",
    headers={"Accept": "application/json"},
).json()

total_learning_resources = len(learning_resources)

print(f"Validating {total_learning_resources} learning resources")

t0 = time.time()

validator = fastjsonschema.compile(schema)

failures = []

for learning_resource in learning_resources[:total_learning_resources]:
    try:
        validator(learning_resource)
    except fastjsonschema.JsonSchemaException as e:
        failures.append(f"Failed at {learning_resource['id']}. Error: {e}, instead of {e.value}")

t1 = time.time()

delta = t1 - t0

if len(failures) > 0:
    for failure in failures:
        print(failure)
    print(f"Validation failed. Time needed: {delta}")
    raise fastjsonschema.JsonSchemaException

print(f"Validation successful. Time needed: {delta}")
