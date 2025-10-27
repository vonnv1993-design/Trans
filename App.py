# app.py - Version WITHOUT Plotly (Simpler)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
import requests
import json
import openpyxl
from io import BytesIO
import hashlib

# Page config
st.set_page_config(
    page_title="Employee Idea Management System",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (same as before)
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .idea-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .status-new {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-review {
        background-color: #fff3e0;
        color: #f57c00;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-approved {
        background-color: #e8f5e9;
        color: #388e3c;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-rejected {
        background-color: #ffebee;
        color: #d32f2f;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-implemented {
        background-color: #f3e5f5;
        color: #7b1fa2;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Data directories
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# File paths
IDEAS_FILE = DATA_DIR / "ideas.xlsx"
USERS_FILE = DATA_DIR / "users.xlsx"
EVALUATIONS_FILE = DATA_DIR / "evaluations.xlsx"
COMMENTS_FILE = DATA_DIR / "comments.xlsx"

# AI API Configuration
LLM_ENDPOINT = "https://llm.blackbox.ai/chat/completions"
LLM_HEADERS = {
    "customerId": "cus_T4SotOIhxreJbK",
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx"
}
MODEL_NAME = "openrouter/claude-sonnet-4"

# Initialize session state
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Data Management Functions
def init_excel_files():
    """Initialize Excel files if they don't exist"""
    
    # Ideas file
    if not IDEAS_FILE.exists():
        ideas_df = pd.DataFrame(columns=[
            'id', 'title', 'description', 'category', 'problem', 'solution',
            'benefits', 'resources', 'submitter', 'submit_date', 'status',
            'upvotes', 'comments_count', 'impact_score', 'feasibility_score',
            'innovation_score', 'strategic_score', 'total_score', 'tags',
            'implementation_date', 'actual_impact', 'cost_savings', 'revenue_impact'
        ])
        ideas_df.to_excel(IDEAS_FILE, index=False)
    
    # Users file
    if not USERS_FILE.exists():
        users_df = pd.DataFrame(columns=[
            'username', 'password', 'email', 'department', 'role',
            'join_date', 'points', 'level', 'badges', 'ideas_submitted',
            'ideas_approved', 'ideas_implemented', 'total_upvotes'
        ])
        # Add default users
        default_users = [
            {
                'username': 'admin',
                'password': hashlib.sha256('admin123'.encode()).hexdigest(),
                'email': 'admin@company.com',
                'department': 'IT',
                'role': 'Admin',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'points': 0,
                'level': 1,
                'badges': '',
                'ideas_submitted': 0,
                'ideas_approved': 0,
                'ideas_implemented': 0,
                'total_upvotes': 0
            },
            {
                'username': 'john_doe',
                'password': hashlib.sha256('demo123'.encode()).hexdigest(),
                'email': 'john@company.com',
                'department': 'Product',
                'role': 'Employee',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'points': 0,
                'level': 1,
                'badges': '',
                'ideas_submitted': 0,
                'ideas_approved': 0,
                'ideas_implemented': 0,
                'total_upvotes': 0
            }
        ]
        users_df = pd.DataFrame(default_users)
        users_df.to_excel(USERS_FILE, index=False)
    
    # Evaluations file
    if not EVALUATIONS_FILE.exists():
        eval_df = pd.DataFrame(columns=[
            'id', 'idea_id', 'evaluator', 'impact_score', 'feasibility_score',
            'innovation_score', 'strategic_score', 'comments', 'date'
        ])
        eval_df.to_excel(EVALUATIONS_FILE, index=False)
    
    # Comments file
    if not COMMENTS_FILE.exists():
        comments_df = pd.DataFrame(columns=[
            'id', 'idea_id', 'username', 'comment', 'date', 'likes'
        ])
        comments_df.to_excel(COMMENTS_FILE, index=False)

def load_data(file_path):
    """Load data from Excel file"""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def save_data(df, file_path):
    """Save data to Excel file"""
    try:
        df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")
        return False

def call_ai_api(prompt, system_prompt):
    """Call AI API for intelligent features"""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(LLM_ENDPOINT, headers=LLM_HEADERS, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        st.error(f"AI API Error: {e}")
        return None

def authenticate(username, password):
    """Authenticate user"""
    users_df = load_data(USERS_FILE)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = users_df[(users_df['username'] == username) & (users_df['password'] == password_hash)]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

def calculate_level(points):
    """Calculate user level based on points"""
    if points < 100:
        return 1, "Innovator"
    elif points < 500:
        return 2, "Explorer"
    elif points < 1500:
        return 3, "Creator"
    elif points < 3000:
        return 4, "Pioneer"
    elif points < 5000:
        return 5, "Visionary"
    else:
        return 6, "Innovation Master"

def award_points(username, points, reason):
    """Award points to user"""
    users_df = load_data(USERS_FILE)
    user_idx = users_df[users_df['username'] == username].index
    if not user_idx.empty:
        users_df.loc[user_idx, 'points'] += points
        current_points = users_df.loc[user_idx, 'points'].values[0]
        level, level_name = calculate_level(current_points)
        users_df.loc[user_idx, 'level'] = level
        save_data(users_df, USERS_FILE)
        st.success(f"🎉 +{points} points for {reason}! (Total: {int(current_points)})")

def get_user_stats(username):
    """Get user statistics"""
    users_df = load_data(USERS_FILE)
    ideas_df = load_data(IDEAS_FILE)
    
    user = users_df[users_df['username'] == username]
    if user.empty:
        return None
    
    user_ideas = ideas_df[ideas_df['submitter'] == username]
    
    stats = {
        'points': int(user['points'].values[0]) if not user.empty else 0,
        'level': int(user['level'].values[0]) if not user.empty else 1,
        'ideas_submitted': len(user_ideas),
        'ideas_approved': len(user_ideas[user_ideas['status'] == 'Approved']),
        'ideas_implemented': len(user_ideas[user_ideas['status'] == 'Implemented']),
        'total_upvotes': int(user_ideas['upvotes'].sum()) if not user_ideas.empty else 0,
        'badges': user['badges'].values[0] if not user.empty and user['badges'].values[0] else ''
    }
    
    level_num, level_name = calculate_level(stats['points'])
    stats['level_name'] = level_name
    
    return stats

# Initialize data
init_excel_files()

# Sidebar - Authentication
with st.sidebar:
    if st.session_state.current_user is None:
        st.header("🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                user = authenticate(username, password)
                if user:
                    st.session_state.current_user = user
                    st.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with col2:
            if st.button("Demo Login", use_container_width=True):
                user = authenticate('john_doe', 'demo123')
                if user:
                    st.session_state.current_user = user
                    st.rerun()
        
        st.divider()
        st.info("""
        **Demo Accounts:**
        - Admin: admin / admin123
        - User: john_doe / demo123
        """)
    
    else:
        user = st.session_state.current_user
        st.success(f"👤 {user['username']}")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🏢 {user['department']} - {user['role']}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.current_user = None
            st.rerun()
        
        st.divider()
        
        # User stats
        stats = get_user_stats(user['username'])
        if stats:
            st.markdown(f"### 🎖️ Level {stats['level']}: {stats['level_name']}")
            st.metric("Points", stats['points'])
            st.progress(min((stats['points'] % 500) / 500, 1.0))
            st.caption(f"{500 - (stats['points'] % 500)} points to next level")
            
            st.divider()
            st.metric("Ideas Submitted", stats['ideas_submitted'])
            st.metric("Ideas Approved", stats['ideas_approved'])
            st.metric("Total Upvotes", stats['total_upvotes'])

# Main content
if st.session_state.current_user is None:
    # Landing page
    st.title("💡 Employee Idea Management System")
    st.markdown("""
    ### Welcome to the Innovation Platform!
    
    This system helps organizations:
    - 📝 **Collect ideas** from employees
    - 🔍 **Evaluate & prioritize** innovations
    - 🎯 **Track implementation** and impact
    - 🏆 **Recognize & reward** contributors
    - 📊 **Measure ROI** of innovation initiatives
    
    **Please login to continue →**
    """)

else:
    # Main app
    user = st.session_state.current_user
    
    # Top navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Dashboard", "💡 Browse Ideas", "➕ Submit Idea", 
        "📊 Analytics", "🏆 Leaderboard", "⚙️ Manage"
    ])
    
    # Load data
    ideas_df = load_data(IDEAS_FILE)
    users_df = load_data(USERS_FILE)
    
    with tab1:
        st.header("📊 Innovation Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ideas", len(ideas_df))
        with col2:
            st.metric("Approved Ideas", len(ideas_df[ideas_df['status'] == 'Approved']))
        with col3:
            st.metric("Implemented", len(ideas_df[ideas_df['status'] == 'Implemented']))
        with col4:
            total_impact = ideas_df['cost_savings'].fillna(0).sum() + ideas_df['revenue_impact'].fillna(0).sum()
            st.metric("Total Impact", f"${total_impact:,.0f}")
        
        st.divider()
        
        # Simple bar charts using Streamlit native
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ideas by Status")
            if not ideas_df.empty:
                status_counts = ideas_df['status'].value_counts()
                st.bar_chart(status_counts)
        
        with col2:
            st.subheader("Ideas by Category")
            if not ideas_df.empty:
                category_counts = ideas_df['category'].value_counts()
                st.bar_chart(category_counts)
        
        st.divider()
        
        # Recent ideas
        st.subheader("🆕 Recent Ideas")
        if not ideas_df.empty:
            recent = ideas_df.sort_values('submit_date', ascending=False).head(5)
            for idx, row in recent.iterrows():
                with st.expander(f"💡 {row['title']} - {row['status']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Category:** {row['category']}")
                        st.write(f"**Submitted by:** {row['submitter']} on {row['submit_date']}")
                        st.write(row['description'][:200] + "...")
                    with col2:
                        st.metric("👍 Upvotes", row['upvotes'])
                        st.metric("💬 Comments", row['comments_count'])
    
    with tab2:
        st.header("💡 Browse Ideas")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.multiselect("Status", 
                ['New', 'Under Review', 'Approved', 'Rejected', 'In Progress', 'Implemented'],
                default=['New', 'Under Review', 'Approved'])
        with col2:
            categories = ['Product', 'Process', 'Customer Experience', 'Technology', 
                         'Cost Reduction', 'Revenue Growth', 'Sustainability', 'Other']
            filter_category = st.multiselect("Category", categories, default=categories)
        with col3:
            sort_by = st.selectbox("Sort by", 
                ['Recent', 'Most Upvoted', 'Highest Score', 'Most Commented'])
        
        # Filter and sort
        filtered_df = ideas_df[
            (ideas_df['status'].isin(filter_status)) & 
            (ideas_df['category'].isin(filter_category))
        ]
        
        if sort_by == 'Recent':
            filtered_df = filtered_df.sort_values('submit_date', ascending=False)
        elif sort_by == 'Most Upvoted':
            filtered_df = filtered_df.sort_values('upvotes', ascending=False)
        elif sort_by == 'Highest Score':
            filtered_df = filtered_df.sort_values('total_score', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('comments_count', ascending=False)
        
        st.write(f"**Showing {len(filtered_df)} ideas**")
        
        # Display ideas
        for idx, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([6, 2, 2])
                
                with col1:
                    st.markdown(f"### 💡 {row['title']}")
                    st.write(row['description'])
                    st.caption(f"📁 {row['category']} | 👤 {row['submitter']} | 📅 {row['submit_date']}")
                
                with col2:
                    status_class = f"status-{row['status'].lower().replace(' ', '-')}"
                    st.markdown(f'<span class="{status_class}">{row["status"]}</span>', 
                              unsafe_allow_html=True)
                    st.metric("👍", row['upvotes'])
                    st.metric("💬", row['comments_count'])
                
                with col3:
                    if st.button("👍 Upvote", key=f"upvote_{idx}"):
                        ideas_df.loc[idx, 'upvotes'] += 1
                        save_data(ideas_df, IDEAS_FILE)
                        award_points(user['username'], 1, "Upvoting idea")
                        st.rerun()
                    
                    if st.button("📖 Details", key=f"view_{idx}"):
                        with st.expander("Idea Details", expanded=True):
                            st.write(f"**Problem:** {row['problem']}")
                            st.write(f"**Solution:** {row['solution']}")
                            st.write(f"**Expected Benefits:** {row['benefits']}")
                            st.write(f"**Resources Needed:** {row['resources']}")
                
                st.divider()
    
    with tab3:
        st.header("➕ Submit New Idea")
        
        with st.form("submit_idea_form"):
            st.subheader("Tell us about your idea!")
            
            title = st.text_input("💡 Idea Title *", 
                placeholder="Give your idea a catchy name")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("📁 Category *", 
                    ['Product', 'Process', 'Customer Experience', 'Technology', 
                     'Cost Reduction', 'Revenue Growth', 'Sustainability', 'Other'])
            
            with col2:
                tags = st.text_input("🏷️ Tags (comma-separated)",
                    placeholder="innovation, automation, customer")
            
            description = st.text_area("📝 Description *",
                placeholder="Describe your idea in detail...",
                height=100)
            
            problem = st.text_area("❓ What problem does this solve? *",
                placeholder="Explain the current problem or pain point...",
                height=80)
            
            solution = st.text_area("✅ Proposed Solution *",
                placeholder="How will your idea solve the problem?",
                height=80)
            
            benefits = st.text_area("🎯 Expected Benefits *",
                placeholder="What value will this create?",
                height=80)
            
            resources = st.text_area("🔧 Resources Needed",
                placeholder="What resources are needed to implement this?",
                height=60)
            
            ai_help = st.checkbox("✨ Use AI to improve my idea description")
            
            submitted = st.form_submit_button("🚀 Submit Idea", use_container_width=True)
            
            if submitted:
                if not title or not description or not problem or not solution or not benefits:
                    st.error("Please fill in all required fields (*)")
                else:
                    # AI enhancement
                    final_description = description
                    if ai_help:
                        with st.spinner("✨ AI is enhancing your idea..."):
                            system_prompt = """You are an innovation consultant helping employees refine their ideas.
                            Improve the clarity, structure, and persuasiveness of idea descriptions.
                            Keep the core message but make it more professional and compelling."""
                            
                            prompt = f"""Improve this idea description:
                            Title: {title}
                            Description: {description}
                            Problem: {problem}
                            Solution: {solution}
                            
                            Provide an enhanced description that is clear, professional, and compelling.
                            Keep it concise (2-3 paragraphs)."""
                            
                            enhanced = call_ai_api(prompt, system_prompt)
                            if enhanced:
                                final_description = enhanced
                                st.success("✅ AI enhanced your description!")
                    
                    # Create new idea
                    new_id = len(ideas_df) + 1
                    new_idea = {
                        'id': new_id,
                        'title': title,
                        'description': final_description,
                        'category': category,
                        'problem': problem,
                        'solution': solution,
                        'benefits': benefits,
                        'resources': resources if resources else 'Not specified',
                        'submitter': user['username'],
                        'submit_date': datetime.now().strftime('%Y-%m-%d'),
                        'status': 'New',
                        'upvotes': 0,
                        'comments_count': 0,
                        'impact_score': 0,
                        'feasibility_score': 0,
                        'innovation_score': 0,
                        'strategic_score': 0,
                        'total_score': 0,
                        'tags': tags,
                        'implementation_date': None,
                        'actual_impact': None,
                        'cost_savings': 0,
                        'revenue_impact': 0
                    }
                    
                    ideas_df = pd.concat([ideas_df, pd.DataFrame([new_idea])], ignore_index=True)
                    save_data(ideas_df, IDEAS_FILE)
                    
                    # Award points
                    award_points(user['username'], 10, "Submitting idea")
                    
                    st.success("🎉 Idea submitted successfully!")
                    st.balloons()
    
    with tab4:
        st.header("📊 Innovation Analytics")
        
        if not ideas_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ideas Over Time")
                ideas_df['submit_date'] = pd.to_datetime(ideas_df['submit_date'])
                ideas_by_month = ideas_df.groupby(ideas_df['submit_date'].dt.to_period('M')).size()
                st.line_chart(ideas_by_month)
            
            with col2:
                st.subheader("Success Rate")
                total = len(ideas_df)
                approved = len(ideas_df[ideas_df['status'].isin(['Approved', 'In Progress', 'Implemented'])])
                st.metric("Approval Rate", f"{(approved/total*100):.1f}%")
                st.progress(approved/total if total > 0 else 0)
    
    with tab5:
        st.header("🏆 Leaderboard")
        
        st.subheader("🌟 Top Innovators")
        
        if not users_df.empty:
            rankings = users_df.sort_values('points', ascending=False).head(10)
            
            for idx, (i, row) in enumerate(rankings.iterrows()):
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                
                with col1:
                    if idx == 0:
                        st.markdown("### 🥇")
                    elif idx == 1:
                        st.markdown("### 🥈")
                    elif idx == 2:
                        st.markdown("### 🥉")
                    else:
                        st.markdown(f"### {idx+1}")
                
                with col2:
                    level, level_name = calculate_level(row['points'])
                    st.markdown(f"**{row['username']}**")
                    st.caption(f"Level {level}: {level_name}")
                
                with col3:
                    st.metric("Points", int(row['points']))
                
                with col4:
                    st.metric("Ideas", int(row['ideas_submitted']))
                
                st.divider()
    
    with tab6:
        st.header("⚙️ Management Dashboard")
        
        if user['role'] != 'Admin':
            st.warning("⚠️ This section is only accessible to administrators.")
        else:
            st.success("👑 Administrator Access")
            
            st.subheader("Ideas Pending Review")
            
            pending = ideas_df[ideas_df['status'].isin(['New', 'Under Review'])]
            
            for idx, row in pending.iterrows():
                with st.expander(f"💡 {row['title']} - {row['status']}"):
                    st.write(f"**Category:** {row['category']}")
                    st.write(f"**Submitted by:** {row['submitter']}")
                    st.write(f"**Description:** {row['description']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{idx}"):
                            ideas_df.loc[idx, 'status'] = 'Approved'
                            save_data(ideas_df, IDEAS_FILE)
                            award_points(row['submitter'], 100, "Idea approved")
                            st.success("Idea approved!")
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Reject", key=f"reject_{idx}"):
                            ideas_df.loc[idx, 'status'] = 'Rejected'
                            save_data(ideas_df, IDEAS_FILE)
                            st.info("Idea rejected")
                            st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>💡 Employee Idea Management System</strong></p>
    <p>Empowering Innovation | Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
