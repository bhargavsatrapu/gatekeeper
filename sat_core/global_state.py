from typing import Dict, List, Any

# Shared global state across modules. Import and update direct  ly.
endpoint_tables: Dict[int, str] =  {}
generated_cases: Dict[str, List[Dict[str, Any]]] = {}

if __name__ == "__main__":
    print("endpoint_tables:", endpoint_tables)
    print("generated_cases:", generated_cases)


