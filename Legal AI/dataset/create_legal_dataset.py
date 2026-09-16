# 4082 Constitution
# 8194 CrPC
# 2267 IPC
# 24600 General Legal
# --------------------
# 39143 total








# import json
# from pathlib import Path


# BASE_DIR = Path(__file__).resolve().parent
# JSON_DIR = BASE_DIR / "json"

# DATASETS = {
#     "constitution_qa.json": "constitution",
#     "crpc_qa.json": "crpc",
#     "ipc_qa.json": "ipc",
#     "gen.json": "general_legal",
# }

# OUTPUT_FILE = JSON_DIR / "legal_knowledge.json"


# def load_json_file(path):
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def main():

#     all_records = []

#     for filename, source in DATASETS.items():

#         path = JSON_DIR / filename

#         print(f"Loading: {filename}")

#         if not path.exists():
#             print(f"ERROR: File not found: {path}")
#             continue

#         data = load_json_file(path)

#         print(f"  Records found: {len(data)}")

#         for item in data:

#             # Handle the first three datasets
#             if "question" in item and "answer" in item:
#                 question = item["question"]
#                 answer = item["answer"]

#             # Handle gen.json
#             elif "Instruction" in item and "Response" in item:
#                 question = item["Instruction"]
#                 answer = item["Response"]

#             else:
#                 print(f"  WARNING: Invalid record in {filename}")
#                 print(f"  Record: {item}")
#                 continue

#             # Basic validation
#             if not question or not answer:
#                 print(f"  WARNING: Empty question/answer in {filename}")
#                 print(f"  Record: {item}")
#                 continue

#             record = {
#                 "question": str(question).strip(),
#                 "answer": str(answer).strip(),
#                 "source": source
#             }

#             all_records.append(record)

#     # Save unified dataset
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         json.dump(
#             all_records,
#             f,
#             ensure_ascii=False,
#             indent=2
#         )

#     print("\n" + "=" * 60)
#     print("LEGAL KNOWLEDGE DATASET CREATED")
#     print("=" * 60)

#     print(f"Total records: {len(all_records)}")
#     print(f"Output: {OUTPUT_FILE}")

#     # Source distribution
#     print("\nSource distribution:")

#     counts = {}

#     for record in all_records:
#         source = record["source"]
#         counts[source] = counts.get(source, 0) + 1

#     for source, count in counts.items():
#         print(f"  {source}: {count}")


# if __name__ == "__main__":
#     main()












# cleaned 


import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(BASE_DIR, "dataset", "json")

FILES = {
    "constitution": "constitution_qa.json",
    "crpc": "crpc_qa.json",
    "ipc": "ipc_qa.json",
    "general_legal": "gen.json",
}

OUTPUT_FILE = os.path.join(JSON_DIR, "legal_knowledge.json")


def clean_text(text):
    """Normalize whitespace and remove unnecessary formatting."""
    if not isinstance(text, str):
        return ""

    return " ".join(text.strip().split())


def load_json(filename):
    path = os.path.join(JSON_DIR, filename)

    print(f"Loading: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"  Records found: {len(data)}")
    return data


def main():

    all_records = []

    # Track exact Q&A duplicates
    seen_qa = set()

    # Statistics
    empty_records = 0
    duplicate_records = 0

    source_counts = {}

    for source, filename in FILES.items():

        data = load_json(filename)

        source_added = 0

        for record in data:

            # Handle different field names
            if source == "general_legal":
                question = record.get("Instruction", "")
                answer = record.get("Response", "")
            else:
                question = record.get("question", "")
                answer = record.get("answer", "")

            # Normalize text
            question = clean_text(question)
            answer = clean_text(answer)

            # Remove empty records
            if not question or not answer:
                empty_records += 1
                continue

            # Exact duplicate detection
            qa_key = (
                question.lower(),
                answer.lower()
            )

            if qa_key in seen_qa:
                duplicate_records += 1
                continue

            seen_qa.add(qa_key)

            # Create standardized record
            cleaned_record = {
                "question": question,
                "answer": answer,
                "source": source
            }

            all_records.append(cleaned_record)
            source_added += 1

        source_counts[source] = source_added

    # Save dataset
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            all_records,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)
    print("CLEANED LEGAL KNOWLEDGE DATASET")
    print("=" * 60)

    print(f"Original records:       {sum(source_counts.values()) + duplicate_records + empty_records}")
    print(f"Empty records removed:  {empty_records}")
    print(f"Duplicate QA removed:   {duplicate_records}")
    print(f"Final records:          {len(all_records)}")

    print("\n" + "=" * 60)
    print("SOURCE DISTRIBUTION")
    print("=" * 60)

    for source in FILES:
        count = sum(
            1
            for record in all_records
            if record["source"] == source
        )

        print(f"{source:<20} {count}")

    print("\n" + "=" * 60)
    print("OUTPUT")
    print("=" * 60)

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()