"""
LLM Service for AI Analytics
Integrates with Ollama (Llama 3.2 3B) for local AI inference
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


class OllamaService:
    """Service to interact with Ollama local LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama service
        
        Args:
            base_url: Ollama API endpoint
            model: Model name (default: llama3.2:3b)
        """
        self.base_url = base_url
        self.model = model
        self.api_endpoint = f"{base_url}/api/generate"
        self.chat_endpoint = f"{base_url}/api/chat"
    
    def check_availability(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None, stream: bool = False) -> str:
        """
        Generate AI response using Ollama
        
        Args:
            prompt: User's question/prompt
            context: Additional context data
            stream: Whether to stream the response
            
        Returns:
            AI generated response text
        """
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\nUser Question: {prompt}\n\nAssistant:",
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                }
            }
            
            # Make API request
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=60,
                stream=stream
            )
            
            if response.status_code == 200:
                if stream:
                    # Handle streaming response
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if 'response' in data:
                                full_response += data['response']
                    return full_response
                else:
                    # Handle non-streaming response
                    data = response.json()
                    return data.get('response', 'No response generated')
            else:
                return f"Error: Unable to generate response (Status: {response.status_code})"
                
        except requests.Timeout:
            return "Error: Request timed out. The model might be processing a complex query."
        except requests.RequestException as e:
            return f"Error: Unable to connect to Ollama. Please ensure Ollama is running. ({str(e)})"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]], context: Optional[Dict] = None) -> str:
        """
        Chat with AI using conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Additional context data
            
        Returns:
            AI generated response
        """
        try:
            # Add system message with context
            system_message = {
                "role": "system",
                "content": self._build_system_prompt(context)
            }
            
            # Prepare messages
            full_messages = [system_message] + messages
            
            payload = {
                "model": self.model,
                "messages": full_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            }
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {}).get('content', 'No response generated')
            else:
                return f"Error: Unable to generate response (Status: {response.status_code})"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build system prompt with context"""
        base_prompt = """You are an AI assistant for ClearView Insurance, specializing in insurance analytics and insights.
Your role is to help users understand their data, provide recommendations, and answer questions about policies, claims, and insurance operations.

Be helpful, professional, and data-driven in your responses. When analyzing data:
- Provide clear insights and patterns
- Suggest actionable recommendations
- Explain trends and anomalies
- Be concise but thorough
- Use specific numbers when available

"""
        
        if not context:
            return base_prompt
        
        # Add role-specific context
        role = context.get('role', 'user')
        
        if role == 'admin':
            base_prompt += """You are assisting an ADMINISTRATOR who oversees the entire insurance system.
Focus on: system-wide analytics, user management insights, compliance, overall performance metrics, and operational efficiency.

"""
        elif role == 'customer':
            base_prompt += """You are assisting a CUSTOMER who wants to understand their insurance policies and claims.
Focus on: personal policy details, claim status, renewal recommendations, coverage explanations, and cost optimization.

"""
        elif role == 'insurer':
            base_prompt += """You are assisting an INSURER who manages policies and claims for their insurance company.
Focus on: policy performance, claims analysis, risk assessment, customer trends, and business insights.

"""
        elif role == 'regulator':
            base_prompt += """You are assisting a REGULATOR who monitors compliance and industry standards.
Focus on: compliance metrics, industry trends, regulatory issues, market oversight, and risk monitoring.

"""
        
        # Add data context
        if 'data_summary' in context:
            base_prompt += f"\n\nCurrent Data Summary:\n{context['data_summary']}\n"
        
        return base_prompt
    
    def generate_data_summary(self, data: Dict) -> str:
        """Generate a formatted data summary for context"""
        summary_parts = []
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                summary_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
            elif isinstance(value, list):
                summary_parts.append(f"- {key.replace('_', ' ').title()}: {len(value)} items")
            elif isinstance(value, dict):
                summary_parts.append(f"- {key.replace('_', ' ').title()}: {len(value)} entries")
        
        return "\n".join(summary_parts)


# Initialize global service instance
ollama_service = OllamaService()


def get_ai_analytics_context(user_type: str, user_id: int, db_models) -> Dict:
    """
    Gather relevant data for AI analytics based on user type
    
    Args:
        user_type: 'admin', 'customer', 'insurer', or 'regulator'
        user_id: User's database ID
        db_models: Dictionary of database model classes
        
    Returns:
        Context dictionary with relevant data
    """
    from models import Admin, Customer, Insurer, Regulator, Policy, Claim, CustomerMonitoredPolicy, CustomerPolicyRequest
    
    context = {
        'role': user_type,
        'timestamp': datetime.now().isoformat()
    }
    
    data = {}
    
    try:
        if user_type == 'admin':
            # Admin gets system-wide statistics
            data['total_customers'] = Customer.query.filter_by(is_active=True).count()
            data['total_insurers'] = Insurer.query.filter_by(is_active=True, is_approved=True).count()
            data['total_regulators'] = Regulator.query.filter_by(is_active=True, is_approved=True).count()
            data['total_policies'] = Policy.query.count()
            data['active_policies'] = Policy.query.filter(
                Policy.status.in_(['Active', 'active'])
            ).count()
            data['total_claims'] = Claim.query.count()
            data['pending_claims'] = Claim.query.filter_by(status='Pending').count()
            data['approved_claims'] = Claim.query.filter_by(status='Approved').count()
            data['rejected_claims'] = Claim.query.filter_by(status='Rejected').count()
            
        elif user_type == 'customer':
            # Customer gets their personal data
            customer = Customer.query.get(user_id)
            if customer:
                owned_policies = Policy.query.filter_by(email_address=customer.email).all()
                monitored = CustomerMonitoredPolicy.query.filter_by(customer_id=user_id).count()
                pending_requests = CustomerPolicyRequest.query.filter_by(
                    customer_id=user_id, 
                    status='pending'
                ).count()
                
                data['owned_policies_count'] = len(owned_policies)
                data['monitored_policies_count'] = monitored
                data['pending_requests'] = pending_requests
                
                # Policy details
                active_policies = [p for p in owned_policies if p.status in ['Active', 'active']]
                data['active_policies_count'] = len(active_policies)
                
                # Claims
                customer_claims = []
                for policy in owned_policies:
                    customer_claims.extend(policy.claims)
                data['total_claims'] = len(customer_claims)
                data['pending_claims'] = len([c for c in customer_claims if c.status == 'Pending'])
                
        elif user_type == 'insurer':
            # Insurer gets their company data
            insurer = Insurer.query.get(user_id)
            if insurer and insurer.insurance_company_id:
                company_policies = Policy.query.filter_by(
                    insurance_company_id=insurer.insurance_company_id
                ).all()
                
                data['total_policies'] = len(company_policies)
                data['active_policies'] = len([p for p in company_policies if p.status in ['Active', 'active']])
                
                # Claims for company policies
                company_claims = []
                for policy in company_policies:
                    company_claims.extend(policy.claims)
                
                data['total_claims'] = len(company_claims)
                data['pending_claims'] = len([c for c in company_claims if c.status == 'Pending'])
                data['approved_claims'] = len([c for c in company_claims if c.status == 'Approved'])
                data['rejected_claims'] = len([c for c in company_claims if c.status == 'Rejected'])
                
                # Customer requests
                customer_requests = CustomerPolicyRequest.query.join(Policy).filter(
                    Policy.insurance_company_id == insurer.insurance_company_id
                ).count()
                data['customer_requests'] = customer_requests
                
        elif user_type == 'regulator':
            # Regulator gets oversight data
            data['total_insurance_companies'] = Insurer.query.filter_by(is_approved=True).count()
            data['total_policies'] = Policy.query.count()
            data['active_policies'] = Policy.query.filter(
                Policy.status.in_(['Active', 'active'])
            ).count()
            data['total_claims'] = Claim.query.count()
            data['high_value_claims'] = Claim.query.filter(
                Claim.claim_amount > 100000
            ).count()
    
    except Exception as e:
        data['error'] = f"Unable to load data: {str(e)}"
    
    context['data_summary'] = ollama_service.generate_data_summary(data)
    context['data'] = data
    
    return context
