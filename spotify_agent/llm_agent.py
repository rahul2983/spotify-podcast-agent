from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Dict, Any, List, Tuple
import logging
import json

logger = logging.getLogger(__name__)

class PodcastLLMAgent:
    """LLM agent for evaluating podcast episodes based on user preferences"""
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o"):
        """Initialize the LLM agent with OpenAI API key"""
        try:
            self.llm = ChatOpenAI(temperature=0, model=model_name, openai_api_key=openai_api_key)
            logger.info(f"LLM agent initialized with model {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM agent: {str(e)}")
            raise
    
    def evaluate_episode_relevance(self, episode_data: Dict[str, Any], 
                                  user_preferences: List[Dict[str, Any]]) -> Tuple[float, str]:
        """
        Evaluate how relevant a podcast episode is to user preferences
        Returns: (relevance_score, reasoning)
        """
        # Extract episode information
        episode_name = episode_data.get('name', '')
        episode_description = episode_data.get('description', '')
        
        # Convert user preferences to string format
        preferences_str = json.dumps(user_preferences, indent=2)
        
        # Prompt template for episode evaluation
        template = """
        You are an AI assistant helping to evaluate podcast episodes for relevance to a user's preferences.
        
        # EPISODE INFORMATION:
        - Title: {episode_name}
        - Description: {episode_description}
        
        # USER PREFERENCES:
        {preferences}
        
        Task: Evaluate how relevant this episode is to the user's preferences.
        First, analyze what topics this episode covers based on the title and description.
        Then, determine how well it matches with the user's podcast preferences.
        
        Please output your evaluation as valid JSON in the following format:
        {{
            "relevance_score": <float between 0.0 and 1.0>,
            "reasoning": "<explanation of your evaluation>",
            "topics_covered": ["<topic1>", "<topic2>", ...],
            "matches_preference": "<which specific preference(s) it matches>"
        }}
        
        Important: Your entire response must be valid JSON only. Do not include any text before or after the JSON.
        """
        
        prompt = PromptTemplate(
            input_variables=["episode_name", "episode_description", "preferences"],
            template=template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            # Get evaluation from the LLM
            result = chain.run(
                episode_name=episode_name,
                episode_description=episode_description,
                preferences=preferences_str
            )
            
            # Debug the raw result
            logger.info(f"Raw LLM result for '{episode_name}': {result[:100]}...")
            
            # Clean the result - sometimes LLM adds markdown code blocks
            result = result.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "", 1)
            if result.endswith("```"):
                result = result.replace("```", "", 1)
            result = result.strip()
            
            # Parse result as JSON
            try:
                evaluation = json.loads(result)
                relevance_score = evaluation.get('relevance_score', 0.0)
                reasoning = evaluation.get('reasoning', '')
                
                return (relevance_score, reasoning)
            except json.JSONDecodeError as je:
                logger.error(f"JSON parsing error: {str(je)} - Raw result: {result[:100]}...")
                # Handle partial episodes - default to higher relevance
                # since we can't properly evaluate
                return (0.75, f"Auto-approved due to parsing error")
                
        except Exception as e:
            logger.error(f"Error evaluating episode relevance: {str(e)}")
            return (0.0, f"Error in evaluation: {str(e)}")
    
    def generate_episode_summary(self, episode_data: Dict[str, Any]) -> str:
        """Generate a concise summary of a podcast episode"""
        # Extract episode information
        episode_name = episode_data.get('name', '')
        episode_description = episode_data.get('description', '')
        
        template = """
        You are an AI assistant that summarizes podcast episodes.
        
        # EPISODE INFORMATION:
        - Title: {episode_name}
        - Description: {episode_description}
        
        Task: Generate a concise summary (maximum 3 sentences) that captures the main topics and value of this episode.
        Your summary should help a user quickly decide if they want to listen to this episode.
        
        Summary:
        """
        
        prompt = PromptTemplate(
            input_variables=["episode_name", "episode_description"],
            template=template
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            summary = chain.run(
                episode_name=episode_name,
                episode_description=episode_description
            )
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating episode summary: {str(e)}")
            return "Summary generation failed."