"""
Workflow nodes for the API Testing Agent.

This module contains all the individual workflow nodes that make up the
LangGraph agent's processing pipeline.
"""

import re
import time
import json
from typing import Dict, Any, List
from config import get_config
from utils.logger import get_logger
from agents.state import AgentState, get_state_manager
from database.models import get_db_initializer, get_endpoint_repository, get_test_case_repository
from parsers.swagger_parser import get_swagger_parser
from generators.test_case_generator import get_test_case_generator, get_test_case_validator
from runners.test_executor import get_test_executor, get_execution_planner
from reporters.test_reporter import get_test_reporter

logger = get_logger(__name__)


class WorkflowNodes:
    """Collection of workflow nodes for the API Testing Agent."""
    
    def __init__(self):
        """Initialize workflow nodes."""
        self.config = get_config()
        self.state_manager = get_state_manager()
        
        # Initialize components
        self.db_initializer = get_db_initializer()
        self.endpoint_repository = get_endpoint_repository()
        self.test_case_repository = get_test_case_repository()
        self.swagger_parser = get_swagger_parser()
        self.test_case_generator = get_test_case_generator()
        self.test_case_validator = get_test_case_validator()
        self.test_executor = get_test_executor()
        self.execution_planner = get_execution_planner()
        self.test_reporter = get_test_reporter()
    
    def initialize_database_node(self, state: AgentState) -> AgentState:
        """
        Initialize the database with required tables.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        print("🔄 [WORKFLOW] Starting database initialization...")
        logger.info("Initializing database")
        self.state_manager.set_current_step("database_initialization")
        
        try:
            print("📊 [DATABASE] Calling database initializer...")
            success = self.db_initializer.initialize_database()
            if success:
                print("✅ [DATABASE] Database initialized successfully")
                logger.info("Database initialized successfully")
                self.state_manager.mark_step_completed("database_initialization")
            else:
                error_msg = "Failed to initialize database"
                print(f"❌ [DATABASE] {error_msg}")
                logger.error(error_msg)
                self.state_manager.add_error(error_msg)
            
            print("🔄 [WORKFLOW] Database initialization node completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Database initialization error: {e}"
            print(f"❌ [ERROR] {error_msg}")
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def parse_swagger_file_node(self, state: AgentState) -> AgentState:
        """
        Parse Swagger/OpenAPI file and extract endpoints.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        print("🔄 [WORKFLOW] Starting Swagger file parsing...")
        logger.info("Parsing Swagger file")
        self.state_manager.set_current_step("endpoint_parsing")
        
        try:
            print(f"📄 [PARSER] Parsing Swagger file: {self.config.swagger_file_path}")
            endpoints = self.swagger_parser.parse_swagger_file(self.config.swagger_file_path)
            
            print(f"📊 [PARSER] Extracted {len(endpoints)} endpoints")
            self.state_manager.update_state(endpoints=endpoints)
            self.state_manager.mark_step_completed("endpoint_parsing")
            
            logger.info(f"Parsed {len(endpoints)} endpoints from Swagger file")
            print("🔄 [WORKFLOW] Swagger parsing node completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Swagger parsing error: {e}"
            print(f"❌ [ERROR] {error_msg}")
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def store_endpoints_node(self, state: AgentState) -> AgentState:
        """
        Store parsed endpoints in the database.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Storing endpoints in database")
        self.state_manager.set_current_step("endpoint_storage")
        
        try:
            endpoints = state["endpoints"]
            stored_count = 0
            
            for endpoint in endpoints:
                success = self.endpoint_repository.insert_endpoint(endpoint)
                if success:
                    stored_count += 1
                else:
                    logger.warning(f"Failed to store endpoint: {endpoint.get('path', 'Unknown')}")
            
            self.state_manager.mark_step_completed("endpoint_storage")
            logger.info(f"Stored {stored_count}/{len(endpoints)} endpoints in database")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Endpoint storage error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def fetch_endpoints_node(self, state: AgentState) -> AgentState:
        """
        Fetch all endpoints from the database.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Fetching endpoints from database")
        print("fetching endpoints")
        try:
            endpoints = self.endpoint_repository.get_all_endpoints()
            self.state_manager.update_state(endpoints=endpoints)
            logger.info(f"Fetched {len(endpoints)} endpoints from database")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Endpoint fetching error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def generate_test_cases_node(self, state: AgentState) -> AgentState:
        """
        Generate test cases for all endpoints.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        print("🔄 [WORKFLOW] Starting test case generation...")
        logger.info("Generating test cases")
        self.state_manager.set_current_step("test_case_generation")
        
        try:
            endpoints = state["endpoints"]
            print(f"🤖 [GENERATOR] Generating test cases for {len(endpoints)} endpoints...")
            generated_cases = self.test_case_generator.generate_test_cases(endpoints)
            
            total_cases = sum(len(cases) for cases in generated_cases.values())
            print(f"✅ [GENERATOR] Generated {total_cases} test cases for {len(generated_cases)} endpoints")
            
            self.state_manager.update_state(generated_cases=generated_cases)
            self.state_manager.mark_step_completed("test_case_generation")
            
            logger.info(f"Generated {total_cases} test cases for {len(generated_cases)} endpoints")
            print("🔄 [WORKFLOW] Test case generation node completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Test case generation error: {e}"
            print(f"❌ [ERROR] {error_msg}")
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def validate_test_cases_node(self, state: AgentState) -> AgentState:
        """
        Validate generated test cases.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Validating test cases")
        self.state_manager.set_current_step("test_case_validation")
        
        try:
            generated_cases = state["generated_cases"]
            feedback = self.test_case_validator.validate_test_cases(generated_cases)
            
            self.state_manager.update_state(feedback=feedback)
            self.state_manager.mark_step_completed("test_case_validation")
            
            logger.info("Test case validation completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Test case validation error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def persist_test_cases_node(self, state: AgentState) -> AgentState:
        """
        Persist test cases to database tables.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Persisting test cases to database")
        self.state_manager.set_current_step("test_case_persistence")
        
        try:
            endpoints = state["endpoints"]
            generated_cases = state["generated_cases"]
            endpoint_tables = {}
            
            for endpoint in endpoints:
                endpoint_id = endpoint["id"]
                method = endpoint["method"]
                path = endpoint["path"]
                endpoint_key = f"{method} {path}"
                
                test_cases = generated_cases.get(endpoint_key, [])
                if not test_cases:
                    continue
                
                # Create table name
                table_name = self._sanitize_table_name(path, method)
                endpoint_tables[endpoint_id] = table_name
                
                # Create table
                success = self.db_initializer.create_test_cases_table(table_name)
                if not success:
                    logger.warning(f"Failed to create table: {table_name}")
                    continue
                
                # Insert test cases
                for test_case in test_cases:
                    test_case["endpoint_id"] = endpoint_id
                    self.test_case_repository.insert_test_case(table_name, test_case)
            
            self.state_manager.update_state(endpoint_tables=endpoint_tables)
            self.state_manager.mark_step_completed("test_case_persistence")
            
            logger.info(f"Persisted test cases to {len(endpoint_tables)} tables")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Test case persistence error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def plan_execution_order_node(self, state: AgentState) -> AgentState:
        """
        Plan the execution order for test cases using LLM.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Planning test execution order")
        self.state_manager.set_current_step("execution_planning")
        
        try:
            import time
            time.sleep(10)  # Delay as in original code
            endpoints = state["endpoints"]
            # Use LLM to plan execution order (matching original implementation)
            planning_prompt = (
                "You are an experienced API test planner.\n"
                "You are given API endpoints in JSON format.\n"
                "Think carefully about dependencies (e.g., register before login, "
                "login before update, create before get/delete).\n"
                "Your job is to decide the most logical execution order for testing.\n"
                "Return ONLY a valid Python list of integers (endpoint IDs).\n\n"
                f"Endpoints:\n{json.dumps(endpoints, indent=2, default=str)}\n\n"
                "Execution order (Python list of int IDs):"
            )
            response = self.execution_planner.client.generate_content(planning_prompt)
            
            logger.info("Raw response:", response.text)
            print("Raw response:", response.text)
            cleaned_output = response.text.strip("`").strip()
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            
            logger.info("Cleaned:", cleaned_output)
            
            try:
                import ast
                execution_order = ast.literal_eval(cleaned_output)
                if not isinstance(execution_order, list):
                    raise ValueError("Execution order is not a list")
                execution_order = [int(x) for x in execution_order]  # ensure all ints
            except Exception as e:
                logger.warning(f"Fallback due to parse error: {e}")
                # fallback: extract numbers manually
                import re
                execution_order = [int(x) for x in re.findall(r"\d+", cleaned_output)]
            
            logger.info(f"Final execution order: {execution_order}, type: {type(execution_order)}")
            self.state_manager.update_state(execution_order=execution_order)
            self.state_manager.mark_step_completed("execution_planning")
            print(f"Final execution order: {self.state_manager.get_state()['execution_order']}, type: {type(execution_order)}")
            logger.info(f"Planned execution order for {len(execution_order)} endpoints")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Execution planning error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def run_positive_flow_node(self, state: AgentState) -> AgentState:
        """
        Execute only positive test cases (first test case from each endpoint).
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        print("🔄 [WORKFLOW] Starting positive flow execution...")
        logger.info("Running positive flow tests")
        self.state_manager.set_current_step("positive_flow_execution")
        
        try:
            # print("⏳ [POSITIVE_FLOW] Waiting 10 seconds before starting...")
            # time.sleep(10)  # Delay as in original code
            
            base_url = self.config.api.base_url
            current_test_state = {
                "request": {},
                "response": {}
            }
            test_execution_order = state["execution_order"]
            endpoint_tables_maps = state["endpoint_tables"]
            
            print(f"📋 [POSITIVE_FLOW] Test execution order: {test_execution_order}")
            print(f"📊 [POSITIVE_FLOW] Endpoint tables: {list(endpoint_tables_maps.keys())}")
            logger.info(f"Test execution order: {test_execution_order}")
            
            for current_id in test_execution_order:
                print(f"🎯 [POSITIVE_FLOW] Processing endpoint ID: {current_id}")
                current_database = endpoint_tables_maps[current_id]
                print(f"📊 [POSITIVE_FLOW] Using database table: {current_database}")
                
                # Get first test case from the table
                test_cases = self.test_case_repository.get_test_cases(current_database)
                if not test_cases:
                    print(f"⚠️ [POSITIVE_FLOW] No test cases found for {current_database}")
                    continue
                    
                first_row = test_cases[0]
                print(f"📋 [POSITIVE_FLOW] First test case: {first_row.get('test_name', 'Unknown')}")
                logger.info(f"First row: {first_row}")
                
                # Extract parts for LLM enrichment
                llm_input = {
                    "url": first_row.get("url", ""),
                    "headers": first_row.get("headers", {}),
                    "query_params": first_row.get("query_params", {}),
                    "input_payload": first_row.get("input_payload", {})
                }
                
                print(f"🤖 [POSITIVE_FLOW] Calling LLM for data generation...")
                print(f"📝 [POSITIVE_FLOW] LLM input: {llm_input}")
                
                # LLM Prompt for data generation (matching original)
                llm_prompt = (
                    "You are a smart test data generator.\n"
                    "I will provide you with API request details that currently contain placeholders.\n"
                    "You also have access to execution logs of previous API calls, which include real responses.\n\n"
                    "Your task is:\n"
                    "1. Replace placeholders with realistic dummy values if the field is independent.\n"
                    "   - Example: username → 'random valid username', email → 'random valid email'.\n"
                    "2. If the field depends on previous API responses (e.g., user_id, token, product_id),\n"
                    "   pick the actual value from the execution logs provided.\n\n"
                    "⚠️ Rules:\n"
                    "- Modify ONLY: url, headers, query_params, input_payload.\n"
                    "- Do not remove or rename fields.\n"
                    "- Keep JSON structure intact.\n"
                    "- If multiple valid values exist in execution logs, just pick one.\n"
                    "- Output must be valid JSON only.\n\n"
                    f"The Base URL of the API server is {base_url}\n"
                    f"Execution Logs:\n{json.dumps(state['execution_logs'], indent=2)}\n\n"
                    f"API Input with placeholders:\n{json.dumps(llm_input, indent=2)}\n\n"
                    "Return JSON with placeholders replaced by actual values.\n"
                    "Use dummy random values for independent fields, but pick dependent fields from execution logs."
                )
                
                response = self.test_executor.data_generator.client.generate_content(llm_prompt)
                print(f"🤖 [POSITIVE_FLOW] LLM response received: {len(response.text)} characters")
                
                try:
                    cleaned_output = response.text.strip("`").strip()
                    if cleaned_output.startswith(("json", "python")):
                        cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
                    enriched_fields = json.loads(cleaned_output)
                    print(f"✅ [POSITIVE_FLOW] Successfully parsed LLM response")
                except Exception as e:
                    print(f"⚠️ [POSITIVE_FLOW] Failed to parse LLM response: {e}")
                    logger.warning(f"Failed to parse LLM response: {e}")
                    enriched_fields = llm_input
                
                # Final JSON with only execution fields
                execution_case = {
                    "url": enriched_fields.get("url", first_row["url"]),
                    "method": first_row["method"],  # method comes from DB, not modified
                    "headers": enriched_fields.get("headers", first_row["headers"]),
                    "query_params": enriched_fields.get("query_params", first_row["query_params"]),
                    "payload": enriched_fields.get("input_payload", first_row["input_payload"])
                }
                
                print("🌐 [POSITIVE_FLOW] Making API call...\n")
                print(f"📤 ############## [API DESCRIPTION] {first_row["test_name"]}#################\n")
                print(f"📤 [POSITIVE_FLOW] Request: {execution_case}")
                logger.info("Hitting API -------------------------------------------")
                logger.info(f"Execution case: {execution_case}")
                
                # Make API call
                api_response = self.test_executor.api_client.make_request(
                    execution_case["method"], 
                    execution_case["url"], 
                    execution_case["headers"],
                    execution_case["query_params"], 
                    execution_case["payload"]
                )
                
                print(f"📥 [POSITIVE_FLOW] Response: {api_response.status_code} in {api_response.execution_time_ms}ms")
                logger.info(f"Response: {api_response.to_dict()}")
                print(f"\nResponse: {api_response.to_dict()}\n")
                current_test_state["request"] = execution_case
                current_test_state["response"] = api_response.to_dict()
                state["execution_logs"][execution_case["url"]] = current_test_state
                print(f"📤 [POSITIVE_FLOW] Responce: {execution_case}")
                print(f"📊 [POSITIVE_FLOW] Execution logs updated: {len(state['execution_logs'])} entries")
                logger.info(f"Execution logs: {state['execution_logs']}")
                logger.info("API execution completed\n\n\n")
                time.sleep(3)
            
            print("✅ [POSITIVE_FLOW] All positive flow tests completed")
            self.state_manager.mark_step_completed("positive_flow_execution")
            logger.info("Positive flow execution completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Positive flow execution error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def run_all_possible_tests_node(self, state: AgentState) -> AgentState:
        """
        Run all possible test cases for each endpoint with detailed execution planning.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        print("🔄 [WORKFLOW] Starting all possible tests execution...")
        logger.info("Running all possible tests for each endpoint")
        self.state_manager.set_current_step("all_tests_execution")
        
        try:
            base_url = self.config.api.base_url
            current_test_state = {
                "request": {},
                "response": {}
            }
            executions_logs = {}
            
            print(f"📊 [ALL_TESTS] Processing {len(state['endpoint_tables'])} endpoint tables...")
            for key, value in state["endpoint_tables"].items():
                executions_logs={}
                print(f"🎯 ##**#****[ALL_TESTS] TESTING NEW END POINT##**#****\n)")
                print(f"🎯 [ALL_TESTS] Processing endpoint table: {value} (ID: {key}\n\n)")
                logger.info(f"Processing endpoint table: {value}")
                
                # Collect extra info from state
                all_endpoints = state.get("endpoints", [])
                table_name = value
                
                # Load testcases for the selected table
                try:
                    all_testcases = self.test_case_repository.get_test_cases(table_name)
                except Exception as e:
                    logger.warning(f"Skipped table {table_name}: {e}")
                    all_testcases = []
                
                # LLM Prompt for ordering (matching original implementation)
                llm_prompt = (
                    "You are an expert API test execution planner.\n"
                    "I will provide you with two things:\n"
                    "1. A list of all available API endpoints with their primary keys.\n"
                    "2. A list of all possible testcases for a single endpoint with their primary keys.\n\n"
                    "Your task:\n"
                    "1. Create the correct execution order for the given endpoint's testcases.\n"
                    "   - If a testcase depends on data (e.g., token, user_id, product_id), "
                    "insert the appropriate provider API(s) from the endpoint list before running it.\n"
                    "   - Auth flows: login must run before protected APIs, logout must run last if applicable.\n"
                    "   - Data dependencies: create/register/add must run before get/update/delete.\n"
                    "   - Negative cases must run after their corresponding positive case.\n"
                    "   - Edge cases should run after positive flows but before destructive cases.\n"
                    "   - Authentication-related negative api tests should run after all tests\n"
                    "2. Use endpoints only for setup (data creation or authentication) if required.\n"
                    "3. Do not drop any testcases. Every testcase must appear exactly once in the final order.\n\n"
                    "⚠️ Rules:\n"
                    "- Return valid JSON only.\n"
                    "- The output must be a list of dictionaries.\n"
                    "- Each dictionary must have exactly one key-value pair.\n"
                    "- Use the key 'all_endpoints' when the entry comes from endpoints.\n"
                    "- Use the key 'all_testcases' when the entry comes from testcases.\n"
                    "- The value must be the primary key of the row (integer).\n\n"
                    f"Here are all endpoints with primary keys:\n{json.dumps(all_endpoints, indent=2, default=str)}\n\n"
                    f"Here are all possible testcases with primary keys:\n{json.dumps(all_testcases, indent=2, default=str)}\n\n"
                    "Return JSON like this:\n"
                    "[\n"
                    "  {\"all_endpoints\": 2},\n"
                    "  {\"all_endpoints\": 101},\n"
                    "  {\"all_testcases\": 7},\n"
                    "  {\"all_testcases\": 201},\n"
                    "  {\"all_endpoints\": 202}\n"
                    "]"
                )
                
                response = self.test_executor.data_generator.client.generate_content(llm_prompt)
                
                try:
                    cleaned_output = response.text.strip("`").strip()
                    if cleaned_output.startswith(("json", "python")):
                        cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
                    execution_order = json.loads(cleaned_output)
                except Exception as e:
                    logger.warning(f"Failed to parse LLM response: {e}")
                    execution_order = []
                
                state["execution_order"] = execution_order
                logger.info(f"Final execution order: {execution_order}")
                
                endpoint_tables_maps = state["endpoint_tables"]
                
                # Execute each item in the execution order
                for item in execution_order:
                    current_test_state = {
                        "request": {},
                        "response": {}
                    }
                    
                    for key, value in item.items():
                        testcase = ""
                        
                        if key == "all_endpoints":
                            current_database = endpoint_tables_maps[value]
                            test_cases = self.test_case_repository.get_test_cases(current_database)
                            if test_cases:
                                testcase = test_cases[0]  # Get first test case
                                
                        elif key == "all_testcases":
                            try:
                                # Load single testcase for the selected table
                                primary_key_column = "id"
                                primary_key_value = value
                                
                                testcase = self.test_case_repository.get_test_case_by_id(table_name, primary_key_value)
                                
                            except Exception as e:
                                logger.warning(f"Skipped table {table_name}: {e}")
                                testcase = None
                        
                        if not testcase:
                            continue
                        
                        # Prepare LLM input
                        llm_input = {
                            "test_descriptsion": testcase.get("test_name", ""),
                            "url": testcase.get("url", ""),
                            "headers": testcase.get("headers", {}),
                            "query_params": testcase.get("query_params", {}),
                            "input_payload": testcase.get("input_payload", {})
                        }
                        
                        # LLM Prompt for test data generation (matching original)
                        llm_prompt = (
                            "You are a smart test data generator for API testing.\n"
                            "I will provide you with API request details containing placeholders, along with execution logs of previous API calls.\n\n"
                            "Your job is to replace the placeholders with values appropriate to the test case type (positive, negative, edge, or auth).\n\n"
                            "Instructions:\n"
                            "1. Positive test cases:\n"
                            "   - Replace placeholders with realistic dummy values if independent (e.g., username → 'valid_user123').\n"
                            "   - If the field depends on previous API responses (e.g., user_id, token), you MUST pick the exact value from the execution logs' 'response' section.\n"
                            "   - For fields requiring uniqueness (like email, username, phone), always generate unique values by appending a timestamp (e.g., 'user_20250915173245', 'test_20250915173245@example.com').\n\n"
                            "2. Negative test cases:\n"
                            "   - Use invalid, malformed, or out-of-range values (e.g., email → 'invalid-email', age → -1, token → 'wrong_token').\n"
                            "   - If the case involves missing fields, set the placeholder to an empty string or null but keep the field name.\n\n"
                            "3. Edge test cases:\n"
                            "   - Use boundary values or extreme inputs (e.g., string length = 0 or very long, max int, special characters).\n"
                            "   - Still keep valid JSON structure.\n\n"
                            "4. Auth test cases:\n"
                            "   - For **valid authentication**, you MUST always extract the token only from the 'response' part of the proper authentication API in execution logs.\n"
                            "   - Ignore tokens found in 'request' or 'url'.\n"
                            "   - Execution logs may also contain expired or invalid tokens in the 'response'. You must only use the valid token from the correct authentication API 'response'.\n"
                            "   - For **invalid authentication**, you may use expired tokens, an empty string, or a deliberately wrong token (e.g., 'wrong_token').\n"
                            "   - Never invent new valid tokens. Always reuse real ones found in the 'response' of execution logs when valid authentication is required.\n\n"
                            "⚠️ Rules:\n"
                            "- Modify ONLY: url, headers, query_params, input_payload.\n"
                            "- Do not remove or rename fields.\n"
                            "- Keep JSON structure intact.\n"
                            "- If multiple valid values exist in execution logs, pick any one.\n"
                            "- Output must be valid JSON only.\n"
                            "- Authentication tokens MUST come only from the 'response' of execution logs, and only from the correct authentication API response when valid authentication is required.\n\n"
                            f"Base URL of the API server: {base_url}, Provided API details contain only endpoints. Please return proper test data.\n\n"
                            f"Execution Logs:\n{json.dumps(executions_logs, indent=2)}\n\n"
                            f"API Input with placeholders:\n{json.dumps(llm_input, indent=2)}\n\n"
                            "Return JSON with placeholders replaced by appropriate values based on the test case type.\n"
                            "Use realistic values for positive cases, invalid/edge/expired values for negative/auth/edge cases.\n"
                        )

                        response = self.test_executor.data_generator.client.generate_content(llm_prompt)
                        
                        try:
                            cleaned_output = response.text.strip("`").strip()
                            if cleaned_output.startswith(("json", "python")):
                                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
                            enriched_fields = json.loads(cleaned_output)
                        except Exception as e:
                            logger.warning(f"Failed to parse LLM response: {e}")
                            enriched_fields = llm_input
                        
                        # Final JSON with only execution fields
                        execution_case = {
                            "url": enriched_fields.get("url", testcase["url"]),
                            "method": testcase["method"],  # method comes from DB, not modified
                            "headers": enriched_fields.get("headers", testcase["headers"]),
                            "query_params": enriched_fields.get("query_params", testcase["query_params"]),
                            "payload": enriched_fields.get("input_payload", testcase["input_payload"])
                        }
                        
                        logger.info("Hitting API -------------------------------------------")
                        logger.info(f"Test name: {testcase['test_name']}")
                        logger.info(f"Execution case: {execution_case}")
                        print("🌐 [RUNNING ENDPOINTS VERIFICATION TESTS] Making API call...\n")
                        print(f"📤 ############## [API DESCRIPTION] {testcase.get("test_name", "")}#################\n")
                        print(f"📤 [POSITIVE_FLOW] Request: {execution_case}")
                        
                        # Make API call
                        api_response = self.test_executor.api_client.make_request(
                            execution_case["method"], 
                            execution_case["url"], 
                            execution_case["headers"],
                            execution_case["query_params"], 
                            execution_case["payload"]
                        )
                        
                        logger.info(f"Response: {api_response.to_dict()}")
                        print(f"\nResponse: {api_response.to_dict()}\n")
                        current_test_state["request"] = execution_case
                        current_test_state["response"] = api_response.to_dict()
                        executions_logs[testcase["test_name"]] = current_test_state
                        
                        logger.info(f"Executions logs: {executions_logs}")
                        logger.info("API execution completed\n\n\n")
                        time.sleep(3)
                print("############ END POINT TESTING COMPLETED ###########\n\n\n\n\n")
            
            self.state_manager.mark_step_completed("all_tests_execution")
            logger.info("All possible tests execution completed")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"All tests execution error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def generate_report_node(self, state: AgentState) -> AgentState:
        """
        Generate test execution report.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        logger.info("Generating test report")
        self.state_manager.set_current_step("report_generation")
        
        try:
            execution_logs = state["execution_logs"]
            
            # Start test suite report
            report = self.test_reporter.start_test_suite("API Test Suite")
            
            # Add execution logs to report
            self.test_reporter.add_execution_logs(execution_logs)
            
            # Finalize report
            final_report = self.test_reporter.finalize_report()
            
            # Generate reports
            json_report = self.test_reporter.generate_json_report("reports/test_results.json")
            text_report = self.test_reporter.generate_text_report("reports/test_results.txt")
            
            # Print summary
            self.test_reporter.print_summary()
            
            # Store results in state
            test_results = {
                "json_report": json_report,
                "text_report": text_report,
                "summary": final_report.summary if final_report else {}
            }
            
            self.state_manager.update_state(test_results=test_results)
            self.state_manager.mark_step_completed("report_generation")
            
            logger.info("Test report generated successfully")
            return self.state_manager.get_state()
            
        except Exception as e:
            error_msg = f"Report generation error: {e}"
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def _sanitize_table_name(self, path: str, method: str) -> str:
        """
        Convert API path + method into a safe SQL table name.
        
        Args:
            path: API path
            method: HTTP method
            
        Returns:
            Sanitized table name
        """
        clean_path = re.sub(r'[^a-zA-Z0-9_]', '_', path.strip("/"))
        return f"api_testcases_{clean_path.lower()}_{method.lower()}"
    
    def should_regenerate_test_cases(self, state: AgentState) -> bool:
        """
        Determine if test cases should be regenerated based on validation feedback.
        
        Args:
            state: Current agent state
            
        Returns:
            True if regeneration is needed, False otherwise
        """
        feedback = state.get("feedback", "")
        return self.test_case_validator.should_regenerate(feedback)


# Global workflow nodes instance
workflow_nodes = WorkflowNodes()


def get_workflow_nodes() -> WorkflowNodes:
    """Get the global workflow nodes instance."""
    return workflow_nodes
