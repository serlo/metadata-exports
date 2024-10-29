import json
from pathlib import PurePath
import time
import fastjsonschema
import requests

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
    timeout=60,
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
        failures.append(
            # pylint: disable=E1101
            f"Failed at {learning_resource['id']} . Error: {e}, instead of {e.value}"
            # pylint: enable=E1101
        )

t1 = time.time()

TIME_INFO = f"Time needed: {t1 - t0}"

TOTAL_FAILURES = len(failures)

if TOTAL_FAILURES > 0:
    for failure in failures:
        print(failure)
    print(f"{TOTAL_FAILURES} validations failed. {TIME_INFO}")
    time.sleep(1)
    raise fastjsonschema.JsonSchemaException

print(f"Validation successful. {TIME_INFO}")
