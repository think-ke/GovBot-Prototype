#!/usr/bin/env python3

import requests
import json

def test_list_documents():
    """Test the list documents endpoint to verify is_indexed field is included."""
    
    url = "http://localhost:5000/documents/"
    headers = {
        "X-API-Key": "admin"
    }
    
    try:
        print("Testing list documents endpoint...")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of documents: {len(data)}")
            
            if data:
                # Check the first document for the is_indexed field
                first_doc = data[0]
                print("\nFirst document fields:")
                for key, value in first_doc.items():
                    print(f"  {key}: {value}")
                
                if 'is_indexed' in first_doc:
                    print("\n✅ SUCCESS: is_indexed field is present!")
                    if 'indexed_at' in first_doc:
                        print("✅ SUCCESS: indexed_at field is also present!")
                    else:
                        print("❌ MISSING: indexed_at field is missing!")
                else:
                    print("\n❌ FAILED: is_indexed field is missing!")
            else:
                print("No documents found to test")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_list_documents()
