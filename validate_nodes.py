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

for learning_resource in learning_resources[:total_learning_resources]:
    validator(learning_resource)

t1 = time.time()

delta = t1 - t0

print(f"Validation successful. Time needed: {delta}")
