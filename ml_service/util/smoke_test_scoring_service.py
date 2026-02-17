"""
Smoke Test for No-Show Scoring Service
======================================
This script tests the deployed scoring endpoint to verify
it's working correctly after deployment.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import os
import json
import requests
import argparse
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential


def get_ml_client() -> MLClient:
    """Create ML client from environment configuration."""
    credential = DefaultAzureCredential()
    
    return MLClient(
        credential=credential,
        subscription_id=os.getenv('SUBSCRIPTION_ID'),
        resource_group_name=os.getenv('RESOURCE_GROUP'),
        workspace_name=os.getenv('WORKSPACE_NAME')
    )


def get_endpoint_url_and_key(ml_client: MLClient, endpoint_name: str) -> tuple:
    """Get endpoint URL and API key."""
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    
    return endpoint.scoring_uri, keys.primary_key


def run_smoke_test(scoring_uri: str, api_key: str, test_data: dict) -> dict:
    """
    Run smoke test against the scoring endpoint.
    
    Args:
        scoring_uri: Endpoint URL
        api_key: API authentication key
        test_data: Test input data
        
    Returns:
        Response from the endpoint
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        scoring_uri,
        headers=headers,
        json=test_data,
        timeout=60
    )
    
    response.raise_for_status()
    return response.json()


def validate_response(response: dict) -> tuple:
    """
    Validate the response from the scoring endpoint.
    
    Args:
        response: Response dictionary
        
    Returns:
        (is_valid, message) tuple
    """
    required_fields = ['no_show_risk', 'risk_category', 'risk_flag']
    
    # Parse if string
    if isinstance(response, str):
        response = json.loads(response)
    
    # Check for errors
    if 'error' in response:
        return False, f"Endpoint returned error: {response['error']}"
    
    # Check required fields
    missing_fields = [f for f in required_fields if f not in response]
    if missing_fields:
        return False, f"Missing fields: {missing_fields}"
    
    # Validate risk score range
    risk = response.get('no_show_risk', -1)
    if not (0 <= risk <= 1):
        return False, f"Invalid risk score: {risk} (expected 0-1)"
    
    # Validate category
    valid_categories = ['Low', 'Medium', 'High', 'Very High']
    category = response.get('risk_category')
    if category not in valid_categories:
        return False, f"Invalid category: {category}"
    
    return True, "Response validated successfully"


def main():
    """Run smoke tests against the deployed endpoint."""
    
    parser = argparse.ArgumentParser(description='Smoke test scoring endpoint')
    parser.add_argument('--endpoint-name', type=str, required=True,
                        help='Name of the online endpoint')
    parser.add_argument('--scoring-uri', type=str, default=None,
                        help='Direct scoring URI (optional)')
    parser.add_argument('--api-key', type=str, default=None,
                        help='API key (optional)')
    
    args = parser.parse_args()
    
    print("=== Running Smoke Tests ===\n")
    
    # Get endpoint details
    if args.scoring_uri and args.api_key:
        scoring_uri = args.scoring_uri
        api_key = args.api_key
    else:
        print("Getting endpoint details from Azure ML...")
        ml_client = get_ml_client()
        scoring_uri, api_key = get_endpoint_url_and_key(ml_client, args.endpoint_name)
    
    print(f"Endpoint: {scoring_uri[:50]}...")
    
    # Define test cases
    test_cases = [
        {
            "name": "Low risk patient",
            "data": {
                "age": 65,
                "scholarship": 0,
                "hipertension": 1,
                "diabetes": 1,
                "alcoholism": 0,
                "handcap": 0,
                "sms_received": 1,
                "lead_time_days": 3,
                "day_of_week": 2,
                "chronic_conditions": 2
            },
            "expected_category": "Low"
        },
        {
            "name": "High risk patient",
            "data": {
                "age": 22,
                "scholarship": 1,
                "hipertension": 0,
                "diabetes": 0,
                "alcoholism": 0,
                "handcap": 0,
                "sms_received": 0,
                "lead_time_days": 30,
                "day_of_week": 4,
                "chronic_conditions": 0
            },
            "expected_category": "High"
        },
        {
            "name": "Medium risk patient",
            "data": {
                "age": 45,
                "scholarship": 0,
                "hipertension": 0,
                "diabetes": 0,
                "alcoholism": 0,
                "handcap": 0,
                "sms_received": 1,
                "lead_time_days": 14,
                "day_of_week": 1,
                "chronic_conditions": 0
            },
            "expected_category": "Medium"
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  Input: {json.dumps(test['data'], indent=2)[:100]}...")
        
        try:
            response = run_smoke_test(scoring_uri, api_key, test['data'])
            is_valid, message = validate_response(response)
            
            if is_valid:
                print(f"  Result: PASS")
                print(f"  Risk: {response.get('no_show_risk', 'N/A'):.2f}")
                print(f"  Category: {response.get('risk_category', 'N/A')}")
                passed += 1
            else:
                print(f"  Result: FAIL - {message}")
                failed += 1
                
        except Exception as e:
            print(f"  Result: FAIL - {str(e)}")
            failed += 1
    
    # Summary
    print(f"\n=== Smoke Test Summary ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(test_cases)}")
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
