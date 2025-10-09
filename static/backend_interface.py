from sat_core.insert_apis_into_db import insert_apis_into_db
from sat_core.generate_test_cases import generate_test_case_and_store_in_db
from sat_core.run_positive_flow import plan_and_run_positive_order
from sat_core.order_testcases import order_testcases_and_execute

def __upload_swagger_document():
    """
    Uploads the Swagger document, extracts all API endpoints,
    and stores them into the database.
    """
    insert_apis_into_db()
    

def __generate_testcases_for_every_endpoint():
    """
    Generates possible test cases (positive, negative, edge, and authentication-related)
    for every API endpoint and stores them in the database.
    """
    generate_test_case_and_store_in_db()


def __run_only_positive_flow():
    """
    Runs a basic positive test for every API endpoint once
    to verify that each endpoint is working correctly before
    proceeding with extensive testing.
    """
    plan_and_run_positive_order()


def __execute_all_test_cases_differnt_endpoint():
    """
    Executes all test cases for the specified endpoints.

    Args:
        Accepts a numeric array as an argument.
        - If the array contains specific endpoint IDs (e.g., [1, 2]),
          it will run all test cases for those endpoints.
        - If the array is empty, it will perform extensive testing
          for all available endpoints.
    """
    order_testcases_and_execute([])