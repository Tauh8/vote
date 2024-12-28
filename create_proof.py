from voting.zk_proof import ZKProof
import random

def test_proof_generation(voter_id, random_value):
    print(f"\nTesting proof generation for voter {voter_id}")
    print(f"Random value: {random_value}")
    
    # 创建零知识证明
    zk = ZKProof()
    
    try:
        # 生成承诺
        commitment = zk.generate_commitment(voter_id, random_value)
        print("\nGenerated commitment:", commitment)
        
        # 生成证明
        proof = zk.create_proof(voter_id, random_value)
        print("\nGenerated proof:", proof)
        
        # 验证证明
        print("\nVerifying proof...")
        result = zk.verify_proof(proof, voter_id)
        print("Verification result:", result)
        
        return result
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return False

def main():
    # Test case 1: Using a valid random value
    print("\n=== Test Case 1: Valid Random Value ===")
    voter_id = "voter5"
    random_value = random.randrange(2**255)  # Generate a random value less than p
    success1 = test_proof_generation(voter_id, random_value)
    
    # Test case 2: Using a different valid random value
    print("\n=== Test Case 2: Different Valid Random Value ===")
    voter_id = "voter6"
    random_value = random.randrange(2**255)
    success2 = test_proof_generation(voter_id, random_value)
    
    # Test case 3: Using same voter_id but different random value
    print("\n=== Test Case 3: Same Voter ID, Different Random Value ===")
    voter_id = "voter5"
    random_value = random.randrange(2**255)
    success3 = test_proof_generation(voter_id, random_value)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Test 1 (Valid Random Value): {'PASSED' if success1 else 'FAILED'}")
    print(f"Test 2 (Different Valid Random Value): {'PASSED' if success2 else 'FAILED'}")
    print(f"Test 3 (Same Voter ID, Different Random Value): {'PASSED' if success3 else 'FAILED'}")

if __name__ == "__main__":
    main()
