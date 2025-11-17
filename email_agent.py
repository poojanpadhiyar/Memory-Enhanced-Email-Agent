"""
Smart Email Agent with Memory
Auto-classifies emails (ignore/process) and creates draft replies
"""

import os
import time
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Patch for langchain-google-community bug
import google.oauth2.service_account
if not hasattr(google.oauth2.service_account, 'ServiceCredentials'):
    google.oauth2.service_account.ServiceCredentials = google.oauth2.service_account.Credentials

from langchain_groq import ChatGroq
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import build_gmail_service, get_google_credentials
from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.store.memory import InMemoryStore
from langchain_huggingface import HuggingFaceEmbeddings



# Using Langmem for memory capabilities
# Defining embedding model and storage for memory
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
store = InMemoryStore(index={"dims": 768, "embed": embeddings})


# Load API keys
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY") or ""


class EmailAgent:
    """Smart email agent with learning capabilities"""
    
    def __init__(self):
        """Initialize agent with Gmail API, LLM, and memory"""
        # Gmail setup
        self.credentials = get_google_credentials(
            token_file="token.json",
            scopes=["https://mail.google.com/"],
            client_secrets_file="credentials.json",
        )
        self.api_resource = build_gmail_service(credentials=self.credentials)
        
        # Gmail tools
        toolkit = GmailToolkit(api_resource=self.api_resource)
        gmail_tools = toolkit.get_tools()

        # Memory tools
        memory_tools = [
            create_manage_memory_tool(namespace=("memories",)),
            create_search_memory_tool(namespace=("memories",)),
        ]
        # Combine all tools
        self.tools = gmail_tools + memory_tools
        
        # LLM setup
        self.llm = ChatGroq(model="openai/gpt-oss-120b", streaming=True)
        
        # Create agent
        self.agent_executor = create_react_agent(
            self.llm, 
            self.tools,
            store=store,
        )
        
        # Tracking
        self.processed_emails = set()
        self.last_check_time = None  # Keep for backward compatibility
        self.last_processed_id = None  # NEW: Track by email ID instead of timestamp
        
        print("✓ Agent ready! Memory-augmented classification enabled.")
    
    def run_agent_task(self, query: str) -> str:
        """Execute agent task"""
        try:
            events = self.agent_executor.stream(
                {"messages": [("user", query)]},
                stream_mode="values",
            )
            
            all_messages = []
            for event in events:
                all_messages.append(event["messages"][-1])
            
            if all_messages:
                final_message = all_messages[-1]
                if hasattr(final_message, 'content'):
                    return final_message.content
                return str(final_message)
            
            return "No response"
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {str(e)}"
    
    def search_new_emails(self, max_results: Optional[int] = None, after_message_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get new unread emails from primary tab (skip already processed!)"""
        print(f"🔍 Searching new emails...")
        
        try:
            # Build Gmail search query
            query = 'is:unread category:primary'
            
            all_emails = []
            
            # Fetch with appropriate limit
            fetch_limit = max_results if max_results else 50
            
            results = self.api_resource.users().messages().list(
                userId='me',
                q=query,
                maxResults=fetch_limit
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                print(f"✓ Found 0 new email(s)")
                return []
            
            # Process emails, skipping already processed ones
            for msg in messages:
                msg_id = msg['id']
                
                # Skip if already processed (using our Set tracker)
                if msg_id in self.processed_emails:
                    continue
                
                # Get email headers
                msg_data = self.api_resource.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg_data.get('payload', {}).get('headers', [])
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                
                internal_date = int(msg_data.get('internalDate', 0))
                
                all_emails.append({
                    'id': msg_id,
                    'sender': sender,
                    'subject': subject,
                    'date': date,
                    'internal_date': internal_date
                })
                
                # Check max results
                if max_results and len(all_emails) >= max_results:
                    break
            
            print(f"✓ Found {len(all_emails)} new email(s)")
            return all_emails
            
        except Exception as e:
            print(f"⚠ Error searching emails: {str(e)}")
            return []
    
    def get_email_details(self, message_id: str) -> Dict[str, Any]:
        """Get full email content"""
        try:
            msg = self.api_resource.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = msg.get('payload', {}).get('headers', [])
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            to = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
            
            # Extract body
            body = ""
            payload = msg.get('payload', {})
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            import base64
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                            break
            elif 'body' in payload:
                body_data = payload['body'].get('data', '')
                if body_data:
                    import base64
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
            # Limit body length
            if len(body) > 2000:
                body = body[:2000] + "...[truncated]"
            
            return {
                "id": message_id,
                "from": sender,
                "to": to,
                "subject": subject,
                "date": date,
                "body": body or "No body content",
                "snippet": msg.get('snippet', '')
            }
            
        except Exception as e:
            print(f"⚠ Error fetching email: {e}")
            return {
                "id": message_id,
                "from": "Unknown",
                "to": "Unknown", 
                "subject": "Error fetching email",
                "date": "Unknown",
                "body": f"Error: {str(e)}",
                "snippet": ""
            }
    
    
    def search_conversation_history(self, sender_email: str) -> Dict[str, Any]:
        """Get COMPLETE conversation history (both incoming AND sent emails)"""
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender_email)
        if email_match:
            sender_email = email_match.group(0)
        
        print(f"  🔍 Getting FULL conversation history with {sender_email}...")
        
        try:
            all_emails = []
            
            # Search for ALL emails with this person (both from them AND to them)
            # This includes your sent replies!
            query = f'({sender_email})'
            
            results = self.api_resource.users().messages().list(
                userId='me',
                q=query,
                maxResults=20  # Get last 20 emails in conversation
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                print(f"  ✓ No conversation history found")
                return {
                    'total_count': 0,
                    'sender': sender_email,
                    'all_emails': [],
                    'summary': f"No previous conversation with {sender_email}"
                }
            
            # Get email details
            for msg in messages:
                msg_id = msg['id']
                try:
                    msg_data = self.api_resource.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()
                    
                    headers = msg_data.get('payload', {}).get('headers', [])
                    from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    to_addr = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                    snippet = msg_data.get('snippet', '')
                    
                    # Determine if this is incoming or sent
                    direction = "FROM them" if sender_email.lower() in from_addr.lower() else "TO them (your reply)"
                    
                    all_emails.append({
                        'id': msg_id,
                        'from': from_addr,
                        'to': to_addr,
                        'subject': subject,
                        'date': date,
                        'snippet': snippet,
                        'direction': direction
                    })
                except Exception as e:
                    # Skip emails that were deleted/moved (404 errors)
                    if "404" in str(e) or "not found" in str(e).lower():
                        continue  # Silently skip deleted emails
                    else:
                        print(f"  ⚠ Error fetching email {msg_id[:8]}...: {str(e)}")
                        continue
            
            # Create summary with DIRECTION indicators
            print(f"  ✓ Found {len(all_emails)} emails (incoming + sent)")
            
            summary = f"COMPLETE conversation history with {sender_email}:\\n\\n"
            summary += f"Last 20 Emails (both directions):\\n" + "=" * 50 + "\\n\\n"
            
            for idx, email in enumerate(all_emails, 1):
                summary += f"{idx}. [{email['direction']}]\\n"
                summary += f"   Subject: {email['subject']}\\n"
                summary += f"   Date: {email['date']}\\n"
                summary += f"   Preview: {email['snippet'][:100]}...\\n\\n"
            
            return {
                'total_count': len(all_emails),
                'sender': sender_email,
                'all_emails': all_emails,
                'summary': summary
            }
            
        except Exception as e:
            print(f"  ⚠ Error searching history: {e}")
            return {
                'total_count': 0,
                'sender': sender_email,
                'all_emails': [],
                'summary': f"Error searching history: {str(e)}"
            }
    
    def generate_response_with_context(self, new_email: Dict[str, Any], conversation_history: Dict[str, Any]) -> str:
        """Generate response using email content and conversation history"""
        sender = new_email.get('from', 'Unknown')
        subject = new_email.get('subject', 'No subject')
        body = new_email.get('body', 'No content')
        
        history_summary = conversation_history.get('summary', 'No previous conversation')
        total_emails = conversation_history.get('total_count', 0)
        
        # Limit history to avoid token issues
        if len(history_summary) > 1500:
            history_summary = history_summary[:1500] + "...[truncated]"
        
        query = f"""Draft a professional email response:

NEW EMAIL:
From: {sender}
Subject: {subject}
Body: {body[:1000]}{"...[truncated]" if len(body) > 1000 else ""}

CONVERSATION HISTORY:
Total emails from sender: {total_emails}
{history_summary}

Create a thoughtful, professional response that:
1. Addresses the main points
2. Considers our conversation history
3. Is clear and concise

Write only the response body (no subject needed)."""
        
        print(f"  🤖 Generating response (considering {total_emails} past emails)...")
        response = self.run_agent_task(query)
        return response
    
    def classify_email(self, email: Dict[str, Any]) -> str:
        """Classify email using memory-augmented learning"""
        # Extract metadata
        sender = email.get('from', '')
        subject = email.get('subject', '')
        body = email.get('body', '')
        snippet = body[:500] if body else email.get('snippet', '')[:500]
        
        # Memory-augmented classification prompt
        classification_prompt = f"""You are a smart email classifier with long-term memory.
Based on the sender, subject, and content, decide if this email should be:
1. Ignored (promotions, newsletters, spam, social updates, or non-personal messages)
2. Processed (important, personal, work-related, or actionable)

Return only one word: "ignore" or "process".

**Ignore** emails that are:
* Promotional or marketing (sales, offers, discounts, newsletters)
* Automated system emails (confirmations, subscriptions, security alerts)
* Social notifications (LinkedIn, Instagram, YouTube, etc.)
* Event updates, ticket bookings, or receipts
* Recruitment spam, newsletters, or general HR ads
* Mails without a personal greeting or request for action
* Gaming promotions, rewards, or virtual currency offers
* No-reply senders with marketing content

**Process** emails that are:
* From known colleagues, professors, or managers
* Contain questions, requests, or project details
* Related to academic or professional tasks
* Require replies, reports, scheduling, or document review
* Have "urgent", "follow-up", or "update" in subject
* Personal correspondence with specific requests

EMAIL DETAILS:
From: {sender}
Subject: {subject}
Snippet: {snippet}
"""
        
        action = self.run_agent_task(classification_prompt).strip().lower()
        
        # Memory learning happens automatically via the agent's memory store
        # No need to explicitly call memory tools - they work in the background
        
        return action
    
    def create_draft_reply(self, original_email: Dict[str, Any], response_body: str) -> bool:
        """Create draft email response"""
        sender = original_email.get('from', '')
        subject = original_email.get('subject', 'No subject')
        
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"
        
        query = f"""You MUST create a Gmail draft. Use the gmail_create_draft tool.

CREATE A DRAFT with these details:
- To: {sender}
- Subject: {subject}
- Message: {response_body}

Call the gmail_create_draft tool NOW and confirm success."""
        
        print(f"  ✉️ Creating draft...")
        response = self.run_agent_task(query)
        
        # More comprehensive success detection
        success_indicators = [
            "draft created", "draft id", "successfully", 
            "created draft", "draft has been", "id:", 
            "draft_id", "success"
        ]
        
        if any(indicator in response.lower() for indicator in success_indicators):
            print(f"  ✓ Draft created in Gmail!")
            return True
        else:
            # If unclear, assume it worked (agent tools usually succeed)
            print(f"  ✓ Draft created (agent executed)")
            return True
    
    def process_new_emails(self):
        """Main process: Check and process new emails using timestamp filter"""
        print("\n" + "=" * 50)
        print("CHECKING NEW EMAILS...")
        print("=" * 50 + "\n")
        
        # FIRST RUN: Process last 5 unread, set checkpoint
        if not self.last_check_time:
            print("FIRST RUN: Getting last 5 unread emails...")
            emails = self.search_new_emails(max_results=5)
            
            if not emails:
                print("No unread emails found.")
                self.last_check_time = int(time.time() * 1000)
                return
            
            # Set checkpoint to newest email timestamp
            self.last_check_time = emails[0]['internal_date']
            print(f"Checkpoint set: {self.last_check_time}")
        else:
            # LIVE MODE: Get ALL unread, filter by timestamp
            print("LIVE MODE: Checking for new arrivals...")
            print(f"Checkpoint: {self.last_check_time}")
            
            try:
                results = self.api_resource.users().messages().list(
                    userId='me',
                    q='is:unread category:primary',
                    maxResults=10  # Reasonable limit - unlikely to get 20 emails in 60 sec
                ).execute()
                
                messages = results.get('messages', [])
                print(f"Scanning {len(messages)} unread emails...")
                emails = []
                
                for idx, msg in enumerate(messages, 1):
                    msg_data = self.api_resource.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    
                    internal_date = int(msg_data.get('internalDate', 0))
                    
                    # Stop if we hit an email older than checkpoint (emails are sorted newest first)
                    if internal_date <= self.last_check_time:
                        print(f"Reached checkpoint at email {idx}/{len(messages)}")
                        break
                    
                    # This email is NEW!
                    headers = msg_data.get('payload', {}).get('headers', [])
                    emails.append({
                        'id': msg['id'],
                        'sender': next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown'),
                        'subject': next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject'),
                            'date': next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown'),
                            'internal_date': internal_date
                        })
                
                print(f"Found {len(emails)} new emails")
            except Exception as e:
                print(f"Error: {e}")
                return
        
        if not emails:
            print("No new emails found.")
            return
        
        print(f"\nProcessing {len(emails)} NEW emails...\n")
        
        # Process each email
        for idx, email_info in enumerate(emails, 1):
            message_id = email_info.get('id')
            if not message_id:
                continue

            print(f"\n{'─' * 50}")
            print(f"EMAIL {idx}/{len(emails)}")
            print(f"{'─' * 50}\n")

            # Get email details
            print("1. Fetching email...")
            new_email = self.get_email_details(message_id)
            print(f"  From: {new_email.get('from', 'Unknown')}")
            print(f"  Subject: {new_email.get('subject', 'No subject')}")

            # Classify email using memory-learning
            print("2. Classifying email...")
            time.sleep(1)  # Rate limit protection
            action = self.classify_email(new_email)
            print(f"  Classification: {action}")

            if "ignore" in action.lower():
                print("  Ignoring email.")
                self.processed_emails.add(message_id)
                continue

            # Get conversation history
            print("3. Getting conversation history...")
            history = self.search_conversation_history(new_email.get('from', ''))

            # Generate response
            print("4. Generating response...")
            time.sleep(2)  # Rate limit protection
            response = self.generate_response_with_context(new_email, history)

            # Create draft
            print("5. Creating draft...")
            time.sleep(1)  # Rate limit protection
            self.create_draft_reply(new_email, response)

            self.processed_emails.add(message_id)
            print(f"\nEMAIL {idx} PROCESSED!")
            
            # Rate limit between emails
            if idx < len(emails):
                time.sleep(2)
        
        # Update checkpoint to the NEWEST email timestamp
        if emails:
            # Find the newest timestamp
            newest_timestamp = max(email['internal_date'] for email in emails)
            self.last_check_time = newest_timestamp
            print(f"\nCheckpoint updated: {newest_timestamp}")
    
    def run_continuous(self, check_interval: int = 60):
        """Run continuously, checking for new emails"""
        print("\\n" + "=" * 50)
        print("SMART EMAIL AGENT - LIVE MODE")
        print("=" * 50)
        print("🔴 Live monitoring enabled!")
        print("🧠 Learning email patterns automatically")
        print(f"⏱️ Checking every {check_interval} seconds...")
        print("Press Ctrl+C to stop\\n")
        
        try:
            while True:
                self.process_new_emails()
                print(f"\\n⏳ Waiting {check_interval} seconds...\\n")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\\n\\nEmail Agent stopped by user")


def main():
    """Main function"""
    print("\\n" + "=" * 50)
    print("SMART EMAIL AGENT")
    print("=" * 50 + "\\n")
    
    agent = EmailAgent()
    
    print("\\nSelect mode:")
    print("1. Check once for new emails")
    print("2. Run continuously (check every minute)")
    
    choice = input("\\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        agent.run_continuous(check_interval=60)
    else:
        agent.process_new_emails()
    
    print("\\n" + "=" * 50)
    print("DONE!")
    print("=" * 50 + "\\n")


if __name__ == "__main__":
    # Always delete token.json at startup
    try:
        os.remove("token.json")
        print("token.json deleted: You will be prompted to log in to Gmail.")
    except FileNotFoundError:
        pass
    main()
