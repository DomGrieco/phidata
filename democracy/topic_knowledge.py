from phi.knowledge.combined import CombinedKnowledgeBase
from phi.vectordb.pgvector import PgVector

class TopicKnowledgeBase:
    def __init__(self, topic: str, db_url: str):
        self.topic = topic
        self.db_url = db_url
        
    def build_topic_query(self) -> str:
        """Build API query for specific topic"""
        base_query = {
            "gun laws": [
                "firearm", "weapon", "second amendment",
                "gun control", "gun rights"
            ],
            "healthcare": [
                "health", "medical", "insurance",
                "medicare", "medicaid"
            ],
            # Add more topic mappings
        }
        
        return " OR ".join(base_query.get(self.topic.lower(), [self.topic])) 