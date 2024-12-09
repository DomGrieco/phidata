from agents.security_agent import SecurityReviewAgent
import asyncio

async def main():
    # Initialize the security agent
    security_agent = SecurityReviewAgent()
    
    # Test code with security issues
    test_code = '''
def connect_to_db():
    password = "super_secret_123"
    username = "admin"
    
    # Unsafe command execution
    import subprocess
    subprocess.call("echo $password", shell=True)
    
    # Potential SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    # Unsafe deserialization
    import pickle
    data = pickle.loads(user_input)
    
    return eval(f"connect({username}, {password})")
'''
    
    print("Running security review...")
    result = await security_agent.review_code(test_code, "test_file.py")
    print("\nSecurity Review Results:")
    print(result)
    
    # Test fix validation
    fixed_code = '''
def connect_to_db():
    import os
    from database import create_connection
    from utils.security import sanitize_input
    
    password = os.environ.get("DB_PASSWORD")
    username = os.environ.get("DB_USERNAME")
    
    # Safe command execution
    import subprocess
    subprocess.run(["echo", password], shell=False)
    
    # Safe parameterized query
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    params = (username, password)
    
    # Safe data handling
    import json
    data = json.loads(user_input)
    
    return create_connection(username, password)
'''
    
    print("\nValidating fixes...")
    validation = await security_agent.validate_fix(test_code, fixed_code)
    print("\nFix Validation Results:")
    print(validation)

if __name__ == "__main__":
    asyncio.run(main()) 