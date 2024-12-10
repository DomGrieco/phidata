"""Runner script for the code review team."""

import asyncio
from ai_code_review.review_team import review_team, review_code

async def main():
    # Example: Review a specific piece of code
    code_to_review = """
def example():
    print("Hello World")
    return None
    """
    
    # Option 1: Quick review
    result = await review_team.run(f"Review this code: {code_to_review}")
    print("Quick Review Result:")
    print(result)
    
    # Option 2: Comprehensive review
    detailed_result = await review_code(code_to_review, "example.py")
    print("\nDetailed Review Result:")
    print(detailed_result)

if __name__ == "__main__":
    asyncio.run(main()) 