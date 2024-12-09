from phi.workflow import Workflow, RunResponse
from phi.storage.workflow.sqlite import SqlWorkflowStorage
from typing import Iterator, Any, ClassVar
from phi.utils.log import logger
from expert_agents import (
    federalism_expert,
    civil_rights_expert, 
    constitutional_expert,
    init_knowledge_bases
)
from historical_agent import congress_analyst
from phi.assistant import Assistant
from phi.agent import Agent
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
import json
import requests
import re

# Define a model for workflow attributes
class CongressWorkflowConfig(BaseModel):
    analyses_dir: Path = Path("democracy/analyses")

class CongressAnalysisWorkflow(Workflow):
    # Class attributes
    query_interpreter: ClassVar[Assistant] = Assistant(
        name="Query Interpreter",
        instructions=[
            "You analyze user queries about congressional legislation and format them for detailed analysis.",
            "Identify the main intent and structure the query appropriately.",
            "Format queries to be specific and detailed for the analysis team."
        ]
    )
    
    # Analysis agents
    congress_analyst: ClassVar[Agent] = congress_analyst
    federalism_expert: ClassVar[Agent] = federalism_expert
    civil_rights_expert: ClassVar[Agent] = civil_rights_expert
    constitutional_expert: ClassVar[Agent] = constitutional_expert
    
    # Final perspective synthesizer
    founding_father_voice: ClassVar[Assistant] = Assistant(
        name="Founding Father Voice",
        instructions=[
            "You are a modern-day founding father with a conservative mindset and witty social media presence.",
            "Key principles to emphasize:",
            "- Individual liberty and freedom above all",
            "- Power belongs to the people, not the government",
            "- States' rights and limited federal power",
            "- Constitutional originalism",
            "- Free market principles",
            "Writing style:",
            "- Use simple, modern language that everyone can understand",
            "- Be witty and engaging like a popular conservative influencer",
            "- Include relevant hashtags (#Constitution, #Liberty, etc.) but not all the time",
            "- Use emojis strategically (🗽 🦅 ⚖️)",
            "- Keep it under 280 characters",
            "- Make complex ideas accessible and relatable",
            "- Reference founding documents but explain them in today's terms",
            "- Add humor but maintain credibility and factual accuracy",
            "- Channel the spirit of Samuel Adams' rebellious nature with modern flair",
            "Tone:",
            "- Confident but not arrogant",
            "- Patriotic but not jingoistic",
            "- Critical of big government",
            "- Pro-individual rights",
            "- Slightly sarcastic when addressing overreach"
        ]
    )
    
    # Config for workflow
    config: CongressWorkflowConfig = CongressWorkflowConfig()

    def __init__(self):
        super().__init__()
        self.storage = SqlWorkflowStorage(
            table_name="congress_workflows",
            db_file="tmp/workflow_storage.db"
        )
        # Initialize knowledge bases
        init_knowledge_bases()
        
        # Create analyses directory
        self.config.analyses_dir.mkdir(exist_ok=True, parents=True)
        
    def save_analysis(self, name: str, content: str, query: str):
        """Save analysis to file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.txt"
        filepath = self.config.analyses_dir / filename
        
        # Use UTF-8 encoding to handle emojis and special characters
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(f"Query: {query}\n\n")
            f.write(content)
            
    def get_amendment_context(self, bill_data: dict) -> str:
        """Get context about what's being amended"""
        try:
            # Check if this bill amends something
            if "amendedBill" in bill_data:
                amended_bill = bill_data["amendedBill"]
                # Construct API query for original bill
                congress = amended_bill.get("congress")
                bill_type = amended_bill.get("type")
                number = amended_bill.get("number")
                
                # Fetch original bill data
                url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{number}?api_key={CONGRESS_API_KEY}"
                response = requests.get(url)
                if response.status_code == 200:
                    original_bill = response.json()
                    return f"""
                    Original Bill Context:
                    Title: {original_bill.get('title')}
                    Status: {original_bill.get('latestAction', {}).get('text')}
                    Summary: {original_bill.get('summary', 'No summary available')}
                    """
            
            # Check if this amends a US Code title
            if "amendments" in bill_data:
                amendments = []
                for amendment in bill_data.get("amendments", []):
                    if amendment.get("type") == "USC":
                        amendments.append(
                            f"Title {amendment.get('title')} Section {amendment.get('section')}"
                        )
                if amendments:
                    return f"This bill amends U.S. Code: {', '.join(amendments)}"
                
            return "No amendment context found"
            
        except Exception as e:
            logger.error(f"Error getting amendment context: {str(e)}")
            return "Error retrieving amendment context"

    def get_bill_details(self, bill_query: str) -> dict:
        """Fetch bill details from Congress.gov API"""
        try:
            # Extract bill info from query (e.g., "H.R. 10329" or "S. 3960")
            bill_match = re.search(r'(?:H\.R\.|S\.)\s*(\d+)', bill_query, re.IGNORECASE)
            if bill_match:
                bill_number = bill_match.group(1)
                bill_type = "hr" if "H.R." in bill_match.group(0) else "s"
                
                # Get current congress number (could be stored or fetched)
                url = f"https://api.congress.gov/v3/bill/118/{bill_type}/{bill_number}?api_key={CONGRESS_API_KEY}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    bill_data = response.json()
                    return {
                        "title": bill_data.get("title", ""),
                        "summary": bill_data.get("summary", ""),
                        "latest_action": bill_data.get("latestAction", {}).get("text", ""),
                        "introduced_date": bill_data.get("introducedDate", ""),
                        "sponsors": bill_data.get("sponsors", []),
                        "committees": bill_data.get("committees", []),
                        "amendments": bill_data.get("amendments", []),
                        "related_bills": bill_data.get("relatedBills", [])
                    }
            return None
                
        except Exception as e:
            logger.error(f"Error fetching bill details: {str(e)}")
            return None

    def run(self, query: str) -> Iterator[RunResponse]:
        """Run the workflow"""
        logger.info(f"Starting analysis workflow for query: {query}")
        
        try:
            # Get bill details if query references specific bill
            bill_details = self.get_bill_details(query)
            
            if bill_details:
                # Add bill context to query
                enhanced_query = f"""
                Query: {query}
                
                Bill Details:
                Title: {bill_details['title']}
                Summary: {bill_details['summary']}
                Latest Action: {bill_details['latest_action']}
                Introduced: {bill_details['introduced_date']}
                """
                
                # Get amendment context if any
                if bill_details.get('amendments'):
                    amendment_context = self.get_amendment_context({'amendments': bill_details['amendments']})
                    enhanced_query += f"\nAmendment Context: {amendment_context}"
                    
                # Use enhanced query for analysis
                query = enhanced_query
            
            # 1. Query interpretation
            interpretation_response = self.query_interpreter.run(
                f"Format this query for congressional analysis: {query}",
                stream=False
            )
            self.save_analysis("query_interpretation", str(interpretation_response), query)
            
            yield RunResponse(
                run_id=self.run_id,
                event="run_response",
                content="🔍 Interpreting query...\n\n" + str(interpretation_response)
            )
            
            # 2. Modern analysis with amendment context
            modern_analysis = ""
            amendment_context = ""
            
            for chunk in self.congress_analyst.run(query, stream=True):
                if hasattr(chunk, 'content') and chunk.content:
                    modern_analysis += chunk.content
                    # Check for bill data in the analysis
                    try:
                        bill_data = json.loads(chunk.content)
                        if isinstance(bill_data, dict):
                            amendment_context = self.get_amendment_context(bill_data)
                    except:
                        pass

            if amendment_context:
                modern_analysis = f"{modern_analysis}\n\n{amendment_context}"
                
            self.save_analysis("modern_analysis", modern_analysis, query)
            yield RunResponse(
                run_id=self.run_id,
                event="run_response",
                content="📊 Modern Analysis:\n\n" + modern_analysis
            )
            
            # 3. Constitutional analysis from different perspectives
            analyses = []
            
            # Federalism perspective
            federalism_response = self.federalism_expert.run(
                f"Analyze the federalism implications of: {modern_analysis}",
                stream=False
            )
            self.save_analysis("federalism_analysis", str(federalism_response), query)
            analyses.append(("Federalism", str(federalism_response)))
            
            # Rights perspective
            rights_response = self.civil_rights_expert.run(
                f"Analyze the rights implications of: {modern_analysis}",
                stream=False
            )
            self.save_analysis("rights_analysis", str(rights_response), query)
            analyses.append(("Rights", str(rights_response)))
            
            # Constitutional structure
            structure_response = self.constitutional_expert.run(
                f"Analyze the constitutional structure implications of: {modern_analysis}",
                stream=False
            )
            self.save_analysis("constitutional_analysis", str(structure_response), query)
            analyses.append(("Structure", str(structure_response)))
            
            # Yield historical analyses
            for title, analysis in analyses:
                yield RunResponse(
                    run_id=self.run_id,
                    event="run_response",
                    content=f"🏛 {title} Analysis:\n\n{analysis}"
                )
            
            # 4. Final synthesis as founding father tweet
            combined_analysis = "\n\n".join([a[1] for a in analyses])
            tweet_response = self.founding_father_voice.run(
                f"""Based on this analysis of modern legislation:
                {modern_analysis}
                
                And these historical perspectives:
                {combined_analysis}
                
                Persona Development:
                    Emulate Elon Musk's style with tweets that are concise, witty, and often provocative. Use humor and irony to make points on liberty, free markets, and innovation.
                    Adopt Donald Trump's bold and direct communication, focusing on strong, opinionated statements that challenge the status quo, with an emphasis on national pride and traditional values.
                    Craft language that aligns with conservative ideologies, highlighting themes of personal responsibility, patriotism, and skepticism towards government expansion.
                Content Creation:
                    Keep tweets short, ideally within the 280-character limit, to maximize impact and shareability.
                    Inject humor or sarcasm to engage followers, often by exaggerating or satirizing current events or political moves.
                    Use rhetorical questions or bold claims to incite discussion, reflecting the influencer's knack for creating buzz.
                Engagement Tactics:
                    Encourage interaction by challenging popular narratives or directly addressing opponents in politics or business.
                    Use hashtags to join or start conversations on trending topics, but sparingly, to avoid seeming too promotional or spammy.
                    Occasionally stir debate by taking a controversial stance or by critiquing current policies or laws in a way that resonates with conservative audiences.
                Specific to the Task:
                    When commenting on legislation or current events:
                    Frame your tweet as if you're the influencer in question, focusing on how they would critique or support the issue based on their public stances or tweets.
                
                Use a blend of humor, directness, and sometimes even shock value, much like Musk's tweets on regulatory overreach or Trump's on policy.
                Include a call to action or a rhetorical flourish that would make the tweet memorable or shareable.
                """,
                stream=False
            )
            
            self.save_analysis("founding_father_tweet", str(tweet_response), query)
            yield RunResponse(
                run_id=self.run_id,
                event="run_response",
                content=f"📜 Founding Father's Tweet:\n\n{str(tweet_response)}"
            )
            
        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}")
            yield RunResponse(
                run_id=self.run_id,
                event="run_response",
                content=f"Error analyzing query: {str(e)}"
            ) 