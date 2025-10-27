# app.py - Complete Employee Idea Management System
import streamlit as st
import pandas as pd
#import plotly.express as px
#import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from pathlib import Path
import requests
import json
from io import BytesIO
import hashlib

# Page config
st.set_page_config(
    page_title="Employee Idea Management System",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .idea-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
    }
    .status-new { background-color: #e3f2fd; color: #1976d2; }
    .status-review { background-color: #fff3e0; color: #f57c00; }
    .status-approved { background-color: #e8f5e9; color: #388e3c; }
    .status-rejected { background-color: #ffebee; color: #d32f2f; }
    .status-progress { background-color: #f3e5f5; color: #7b1fa2; }
    .status-implemented { background-color: #c8e6c9; color: #2e7d32; }
    .level-badge {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #000;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'ideas_df' not in st.session_state:
    st.session_state.ideas_df = pd.DataFrame()
if 'users_df' not in st.session_state:
    st.session_state.users_df = pd.DataFrame()
if 'comments_df' not in st.session_state:
    st.session_state.comments_df = pd.DataFrame()

# AI API Configuration
LLM_ENDPOINT = "https://llm.blackbox.ai/chat/completions"
LLM_HEADERS = {
    "customerId": "cus_T4SotOIhxreJbK",
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx"
}
MODEL_NAME = "openrouter/claude-sonnet-4"

# Helper Functions
def init_data():
    """Initialize data structures"""
    if st.session_state.users_df.empty:
        st.session_state.users_df = pd.DataFrame([
            {
                'username': 'admin',
                'password': hashlib.sha256('admin123'.encode()).hexdigest(),
                'email': 'admin@company.com',
                'department': 'IT',
                'role': 'Admin',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'points': 0,
                'level': 1,
                'ideas_submitted': 0,
                'ideas_approved': 0
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
                'ideas_submitted': 0,
                'ideas_approved': 0
            },
            {
                'username': 'jane_smith',
                'password': hashlib.sha256('demo123'.encode()).hexdigest(),
                'email': 'jane@company.com',
                'department': 'Marketing',
                'role': 'Employee',
                'join_date': datetime.now().strftime('%Y-%m-%d'),
                'points': 250,
                'level': 2,
                'ideas_submitted': 3,
                'ideas_approved': 1
            }
        ])
    
    if st.session_state.ideas_df.empty:
        # Create sample ideas
        sample_ideas = [
            {
                'id': 1,
                'title': 'AI-Powered Customer Support Chatbot',
                'description': 'Implement an intelligent chatbot to handle common customer queries 24/7, reducing response time and support costs.',
                'category': 'Technology',
                'problem': 'Customer support team is overwhelmed with repetitive questions, leading to slow response times.',
                'solution': 'Deploy an AI chatbot trained on our FAQ and historical support tickets to answer common questions instantly.',
                'benefits': 'Reduce support costs by 40%, improve response time from hours to seconds, increase customer satisfaction.',
                'resources': '2 developers for 3 months, $50K budget for AI platform',
                'submitter': 'john_doe',
                'submit_date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                'status': 'Approved',
                'upvotes': 23,
                'comments_count': 5,
                'impact_score': 9,
                'feasibility_score': 7,
                'innovation_score': 8,
                'strategic_score': 9,
                'total_score': 33,
                'tags': 'AI, automation, customer service',
                'cost_savings': 120000,
                'revenue_impact': 0
            },
            {
                'id': 2,
                'title': 'Employee Wellness Program',
                'description': 'Launch a comprehensive wellness program including gym memberships, mental health support, and healthy snacks.',
                'category': 'Process',
                'problem': 'Employee burnout and health issues leading to increased sick days and turnover.',
                'solution': 'Partner with local gyms, provide mental health counseling, stock office with healthy snacks.',
                'benefits': 'Reduce sick days by 25%, improve employee satisfaction, lower healthcare costs.',
                'resources': '$100K annual budget, HR coordinator',
                'submitter': 'jane_smith',
                'submit_date': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                'status': 'Under Review',
                'upvotes': 18,
                'comments_count': 3,
                'impact_score': 7,
                'feasibility_score': 8,
                'innovation_score': 5,
                'strategic_score': 8,
                'total_score': 28,
                'tags': 'wellness, culture, retention',
                'cost_savings': 50000,
                'revenue_impact': 0
            },
            {
                'id': 3,
                'title': 'Mobile App for Product Ordering',
                'description': 'Develop a mobile app to allow customers to browse and order products on-the-go.',
                'category': 'Product',
                'problem': 'Customers want to shop from mobile devices but our website is not mobile-optimized.',
                'solution': 'Build native iOS and Android apps with seamless ordering experience.',
                'benefits': 'Increase mobile sales by 60%, improve customer retention, expand market reach.',
                'resources': '3 developers for 6 months, $150K budget',
                'submitter': 'john_doe',
                'submit_date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                'status': 'New',
                'upvotes': 12,
                'comments_count': 2,
                'impact_score': 0,
                'feasibility_score': 0,
                'innovation_score': 0,
                'strategic_score': 0,
                'total_score': 0,
                'tags': 'mobile, app, ecommerce',
                'cost_savings': 0,
                'revenue_impact': 300000
            },
            {
                'id': 4,
                'title': 'Green Office Initiative',
                'description': 'Implement eco-friendly practices including solar panels, recycling programs, and paperless workflows.',
                'category': 'Sustainability',
                'problem': 'High energy costs and environmental impact from office operations.',
                'solution': 'Install solar panels, set up comprehensive recycling, digitize all documents.',
                'benefits': 'Reduce energy costs by 30%, improve brand reputation, meet sustainability goals.',
                'resources': '$200K upfront investment, facilities team',
                'submitter': 'jane_smith',
                'submit_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                'status': 'New',
                'upvotes': 15,
                'comments_count': 4,
                'impact_score': 0,
                'feasibility_score': 0,
                'innovation_score': 0,
                'strategic_score': 0,
                'total_score': 0,
                'tags': 'sustainability, cost reduction, environment',
                'cost_savings': 80000,
                'revenue_impact': 0
            },
            {
                'id': 5,
                'title': 'Referral Reward Program',
                'description': 'Create a customer referral program offering discounts for successful referrals.',
                'category': 'Revenue Growth',
                'problem': 'Customer acquisition costs are high and marketing ROI is declining.',
                'solution': 'Offer 20% discount to customers who refer friends who make a purchase.',
                'benefits': 'Reduce acquisition cost by 50%, increase customer lifetime value, viral growth.',
                'resources': 'Marketing team, $30K budget for rewards',
                'submitter': 'john_doe',
                'submit_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'status': 'Approved',
                'upvotes': 20,
                'comments_count': 6,
                'impact_score': 8,
                'feasibility_score': 9,
                'innovation_score': 6,
                'strategic_score': 8,
                'total_score': 31,
                'tags': 'marketing, growth, referral',
                'cost_savings': 0,
                'revenue_impact': 250000
            }
        ]
        st.session_state.ideas_df = pd.DataFrame(sample_ideas)
    
    if st.session_state.comments_df.empty:
        st.session_state.comments_df = pd.DataFrame([
            {
                'id': 1,
                'idea_id': 1,
                'username': 'jane_smith',
                'comment': 'Great idea! We should integrate this with our CRM system.',
                'date': (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'),
                'likes': 5
            },
            {
                'id': 2,
                'idea_id': 1,
                'username': 'admin',
                'comment': 'Approved for Q2 implementation. Team assigned.',
                'date': (datetime.now() - timedelta(days=13)).strftime('%Y-%m-%d'),
                'likes': 8
            }
        ])

def authenticate(username, password):
    """Authenticate user"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = st.session_state.users_df[
        (st.session_state.users_df['username'] == username) & 
        (st.session_state.users_df['password'] == password_hash)
    ]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

def calculate_level(points):
    """Calculate user level"""
    if points < 100:
        return 1, "Innovator", "🌱"
    elif points < 500:
        return 2, "Explorer", "🔍"
    elif points < 1500:
        return 3, "Creator", "🎨"
    elif points < 3000:
        return 4, "Pioneer", "🚀"
    elif points < 5000:
        return 5, "Visionary", "🔮"
    else:
        return 6, "Innovation Master", "👑"

def award_points(username, points, reason):
    """Award points to user"""
    idx = st.session_state.users_df[st.session_state.users_df['username'] == username].index
    if not idx.empty:
        st.session_state.users_df.loc[idx, 'points'] += points
        current_points = st.session_state.users_df.loc[idx, 'points'].values[0]
        level, level_name, emoji = calculate_level(current_points)
        st.session_state.users_df.loc[idx, 'level'] = level
        st.toast(f"🎉 +{points} points for {reason}!", icon="⭐")

def call_ai_api(prompt, system_prompt):
    """Call AI API"""
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
        return None
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None

def get_user_stats(username):
    """Get user statistics"""
    user = st.session_state.users_df[st.session_state.users_df['username'] == username]
    if user.empty:
        return None
    
    user_ideas = st.session_state.ideas_df[st.session_state.ideas_df['submitter'] == username]
    
    points = int(user['points'].values[0])
    level, level_name, emoji = calculate_level(points)
    
    return {
        'points': points,
        'level': level,
        'level_name': level_name,
        'emoji': emoji,
        'ideas_submitted': len(user_ideas),
        'ideas_approved': len(user_ideas[user_ideas['status'].isin(['Approved', 'In Progress', 'Implemented'])]),
        'total_upvotes': int(user_ideas['upvotes'].sum()) if not user_ideas.empty else 0
    }

# Initialize data
init_data()

# Sidebar
with st.sidebar:
    st.image("https://storage.googleapis.com/workspace-0f70711f-8b4e-4d94-86f1-2a93ccde5887/image/f235bec8-f887-4b36-90ac-79a4c25cd446.png", use_container_width=True)
    
    if st.session_state.current_user is None:
        st.header("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col1, col2 = st.columns(2)
            with col1:
                login = st.form_submit_button("Login", use_container_width=True)
            with col2:
                demo = st.form_submit_button("Demo", use_container_width=True)
            
            if login:
                user = authenticate(username, password)
                if user:
                    st.session_state.current_user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
            if demo:
                user = authenticate('john_doe', 'demo123')
                if user:
                    st.session_state.current_user = user
                    st.rerun()
        
        st.divider()
        st.info("""
        **📝 Demo Accounts:**
        
        **Admin:**
        - Username: `admin`
        - Password: `admin123`
        
        **Employees:**
        - Username: `john_doe`
        - Password: `demo123`
        
        - Username: `jane_smith`
        - Password: `demo123`
        """)
    
    else:
        user = st.session_state.current_user
        stats = get_user_stats(user['username'])
        
        st.success(f"👤 **{user['username']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🏢 {user['department']} • {user['role']}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.current_user = None
            st.rerun()
        
        st.divider()
        
        if stats:
            st.markdown(f"""
            <div class="level-badge">
                {stats['emoji']} Level {stats['level']}: {stats['level_name']}
            </div>
            """, unsafe_allow_html=True)
            
            st.metric("⭐ Points", stats['points'])
            next_level_points = [100, 500, 1500, 3000, 5000, 10000][stats['level']-1] if stats['level'] < 6 else 10000
            progress = min((stats['points'] % next_level_points) / next_level_points, 1.0) if stats['level'] < 6 else 1.0
            st.progress(progress)
            
            if stats['level'] < 6:
                remaining = next_level_points - (stats['points'] % next_level_points)
                st.caption(f"🎯 {remaining} points to next level")
            else:
                st.caption("🏆 Maximum level reached!")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            col1.metric("💡 Ideas", stats['ideas_submitted'])
            col2.metric("✅ Approved", stats['ideas_approved'])
            st.metric("👍 Upvotes", stats['total_upvotes'])

# Main App
if st.session_state.current_user is None:
    # Landing Page
    st.title("💡 Employee Idea Management System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 Transform Your Organization Through Innovation
        
        Empower every employee to contribute ideas and drive meaningful change.
        
        #### ✨ Key Features:
        
        - **💡 Idea Submission** - Easy-to-use forms with AI enhancement
        - **🎯 Smart Evaluation** - Multi-criteria scoring system
        - **🏆 Gamification** - Points, levels, badges, and leaderboards
        - **📊 Impact Tracking** - Measure ROI and business value
        - **🤝 Collaboration** - Comments, upvotes, and discussions
        - **📈 Analytics** - Real-time dashboards and insights
        
        #### 💰 Proven Results:
        
        - **3x** more employee engagement
        - **$500K+** in cost savings per year
        - **40%** faster time to market for innovations
        - **85%** employee participation rate
        
        #### 🎮 Gamification That Works:
        
        - Earn points for every contribution
        - Unlock achievements and badges
        - Compete on leaderboards
        - Progress through 6 levels of mastery
        
        ---
        
        **👈 Login now to get started!**
        """)
    
    with col2:
        st.image("https://storage.googleapis.com/workspace-0f70711f-8b4e-4d94-86f1-2a93ccde5887/image/c9c387f8-f61e-4b6e-8ce4-739515e0038f.png", use_container_width=True)
        
        st.markdown("""
        ### 📈 Success Stories
        
        **AI Chatbot** 💬
        *Reduced support costs by 40%*
        
        **Wellness Program** 🏃
        *Decreased sick days by 25%*
        
        **Mobile App** 📱
        *Increased sales by 60%*
        
        **Referral Program** 🤝
        *Cut acquisition costs by 50%*
        """)

else:
    # Main Application
    user = st.session_state.current_user
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Dashboard",
        "💡 Browse Ideas",
        "➕ Submit Idea",
        "📊 Analytics",
        "🏆 Leaderboard",
        "⚙️ Admin"
    ])
    
    with tab1:
        st.title("📊 Innovation Dashboard")
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ideas = len(st.session_state.ideas_df)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0;font-size:2rem;">{total_ideas}</h3>
                <p style="margin:5px 0 0 0;opacity:0.9;">Total Ideas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            approved = len(st.session_state.ideas_df[st.session_state.ideas_df['status'].isin(['Approved', 'In Progress', 'Implemented'])])
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);">
                <h3 style="margin:0;font-size:2rem;">{approved}</h3>
                <p style="margin:5px 0 0 0;opacity:0.9;">Approved</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            implemented = len(st.session_state.ideas_df[st.session_state.ideas_df['status'] == 'Implemented'])
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);">
                <h3 style="margin:0;font-size:2rem;">{implemented}</h3>
                <p style="margin:5px 0 0 0;opacity:0.9;">Implemented</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_impact = st.session_state.ideas_df['cost_savings'].fillna(0).sum() + st.session_state.ideas_df['revenue_impact'].fillna(0).sum()
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);">
                <h3 style="margin:0;font-size:2rem;">${total_impact/1000:.0f}K</h3>
                <p style="margin:5px 0 0 0;opacity:0.9;">Total Impact</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ideas by Status")
            status_counts = st.session_state.ideas_df['status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📁 Ideas by Category")
            category_counts = st.session_state.ideas_df['category'].value_counts()
            fig = px.bar(
                x=category_counts.values,
                y=category_counts.index,
                orientation='h',
                color=category_counts.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                height=350,
                margin=dict(t=30, b=0, l=0, r=0),
                showlegend=False,
                xaxis_title="Count",
                yaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Recent Ideas
        st.subheader("🆕 Recent Ideas")
        recent = st.session_state.ideas_df.sort_values('submit_date', ascending=False).head(5)
        
        for idx, row in recent.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([6, 2, 2])
                
                with col1:
                    st.markdown(f"### 💡 {row['title']}")
                    st.write(row['description'][:150] + "...")
                    st.caption(f"📁 {row['category']} • 👤 {row['submitter']} • 📅 {row['submit_date']}")
                
                with col2:
                    status_map = {
                        'New': 'status-new',
                        'Under Review': 'status-review',
                        'Approved': 'status-approved',
                        'Rejected': 'status-rejected',
                        'In Progress': 'status-progress',
                        'Implemented': 'status-implemented'
                    }
                    st.markdown(f'<span class="status-badge {status_map.get(row["status"], "status-new")}">{row["status"]}</span>', unsafe_allow_html=True)
                    st.metric("👍 Upvotes", row['upvotes'])
                
                with col3:
                    st.metric("💬 Comments", row['comments_count'])
                    if row['total_score'] > 0:
                        st.metric("⭐ Score", f"{row['total_score']}/40")
                
                st.divider()
    
    with tab2:
        st.title("💡 Browse Ideas")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_status = st.multiselect(
                "Status",
                ['New', 'Under Review', 'Approved', 'Rejected', 'In Progress', 'Implemented'],
                default=['New', 'Under Review', 'Approved', 'In Progress']
            )
        
        with col2:
            categories = st.session_state.ideas_df['category'].unique().tolist()
            filter_category = st.multiselect(
                "Category",
                categories,
                default=categories
            )
        
        with col3:
            filter_submitter = st.selectbox(
                "Submitter",
                ['All'] + st.session_state.ideas_df['submitter'].unique().tolist()
            )
        
        with col4:
            sort_by = st.selectbox(
                "Sort by",
                ['Recent', 'Most Upvoted', 'Highest Score', 'Most Commented']
            )
        
        # Filter ideas
        filtered = st.session_state.ideas_df[
            (st.session_state.ideas_df['status'].isin(filter_status)) &
            (st.session_state.ideas_df['category'].isin(filter_category))
        ]
        
        if filter_submitter != 'All':
            filtered = filtered[filtered['submitter'] == filter_submitter]
        
        # Sort
        if sort_by == 'Recent':
            filtered = filtered.sort_values('submit_date', ascending=False)
        elif sort_by == 'Most Upvoted':
            filtered = filtered.sort_values('upvotes', ascending=False)
        elif sort_by == 'Highest Score':
            filtered = filtered.sort_values('total_score', ascending=False)
        else:
            filtered = filtered.sort_values('comments_count', ascending=False)
        
        st.info(f"📋 Showing **{len(filtered)}** ideas")
        
        # Display ideas
        for idx, row in filtered.iterrows():
            with st.container():
                col1, col2 = st.columns([7, 3])
                
                with col1:
                    st.markdown(f"### 💡 {row['title']}")
                    st.write(row['description'])
                    
                    with st.expander("📖 View Full Details"):
                        st.markdown(f"**❓ Problem:**")
                        st.write(row['problem'])
                        st.markdown(f"**✅ Solution:**")
                        st.write(row['solution'])
                        st.markdown(f"**🎯 Expected Benefits:**")
                        st.write(row['benefits'])
                        st.markdown(f"**🔧 Resources Needed:**")
                        st.write(row['resources'])
                        
                        if row['total_score'] > 0:
                            st.divider()
                            st.markdown("**📊 Evaluation Scores:**")
                            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                            score_col1.metric("Impact", f"{row['impact_score']}/10")
                            score_col2.metric("Feasibility", f"{row['feasibility_score']}/10")
                            score_col3.metric("Innovation", f"{row['innovation_score']}/10")
                            score_col4.metric("Strategy", f"{row['strategic_score']}/10")
                        
                        # Comments section
                        st.divider()
                        st.markdown("**💬 Comments:**")
                        idea_comments = st.session_state.comments_df[st.session_state.comments_df['idea_id'] == row['id']]
                        if not idea_comments.empty:
                            for _, comment in idea_comments.iterrows():
                                st.markdown(f"""
                                <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0;">
                                    <strong>{comment['username']}</strong> • {comment['date']}
                                    <p style="margin: 8px 0 0 0;">{comment['comment']}</p>
                                    <small>👍 {comment['likes']} likes</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Add comment
                        new_comment = st.text_area("Add a comment", key=f"comment_{idx}")
                        if st.button("💬 Post Comment", key=f"post_{idx}"):
                            if new_comment:
                                new_comment_data = {
                                    'id': len(st.session_state.comments_df) + 1,
                                    'idea_id': row['id'],
                                    'username': user['username'],
                                    'comment': new_comment,
                                    'date': datetime.now().strftime('%Y-%m-%d'),
                                    'likes': 0
                                }
                                st.session_state.comments_df = pd.concat([
                                    st.session_state.comments_df,
                                    pd.DataFrame([new_comment_data])
                                ], ignore_index=True)
                                
                                # Update comment count
                                st.session_state.ideas_df.loc[idx, 'comments_count'] += 1
                                
                                award_points(user['username'], 2, "commenting on idea")
                                st.success("Comment posted!")
                                st.rerun()
                
                with col2:
                    status_map = {
                        'New': 'status-new',
                        'Under Review': 'status-review',
                        'Approved': 'status-approved',
                        'Rejected': 'status-rejected',
                        'In Progress': 'status-progress',
                        'Implemented': 'status-implemented'
                    }
                    st.markdown(f'<span class="status-badge {status_map.get(row["status"], "status-new")}">{row["status"]}</span>', unsafe_allow_html=True)
                    
                    st.caption(f"📁 {row['category']}")
                    st.caption(f"👤 {row['submitter']}")
                    st.caption(f"📅 {row['submit_date']}")
                    
                    st.divider()
                    
                    col_a, col_b = st.columns(2)
                    col_a.metric("👍", row['upvotes'])
                    col_b.metric("💬", row['comments_count'])
                    
                    if st.button("👍 Upvote", key=f"upvote_{idx}", use_container_width=True):
                        st.session_state.ideas_df.loc[idx, 'upvotes'] += 1
                        award_points(user['username'], 1, "upvoting")
                        st.rerun()
                
                st.divider()
    
    with tab3:
        st.title("➕ Submit New Idea")
        
        with st.form("submit_idea_form", clear_on_submit=True):
            st.subheader("💡 Tell us about your innovation!")
            
            title = st.text_input(
                "Idea Title *",
                placeholder="Give your idea a catchy, descriptive name"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox(
                    "Category *",
                    ['Product', 'Process', 'Customer Experience', 'Technology',
                     'Cost Reduction', 'Revenue Growth', 'Sustainability', 'Other']
                )
            with col2:
                tags = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="innovation, automation, AI"
                )
            
            description = st.text_area(
                "Description *",
                placeholder="Describe your idea in detail. What is it and how does it work?",
                height=100
            )
            
            problem = st.text_area(
                "What problem does this solve? *",
                placeholder="Explain the current pain point, challenge, or opportunity",
                height=80
            )
            
            solution = st.text_area(
                "Proposed Solution *",
                placeholder="How will your idea solve the problem? Be specific about implementation",
                height=80
            )
            
            benefits = st.text_area(
                "Expected Benefits *",
                placeholder="What value will this create? (cost savings, revenue, efficiency, customer satisfaction, etc.)",
                height=80
            )
            
            resources = st.text_area(
                "Resources Needed",
                placeholder="What resources are needed? (people, budget, time, tools, technology)",
                height=60
            )
            
            st.divider()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                ai_enhance = st.checkbox("✨ Use AI to enhance my idea description")
            with col2:
                submit = st.form_submit_button("🚀 Submit Idea", use_container_width=True)
            
            if submit:
                if not all([title, description, problem, solution, benefits]):
                    st.error("❌ Please fill in all required fields (*)")
                else:
                    final_description = description
                    
                    if ai_enhance:
                        with st.spinner("✨ AI is enhancing your idea..."):
                            system_prompt = """You are an innovation consultant. Improve idea descriptions to be clear, compelling, and professional. Maintain the core message but enhance structure, clarity, and persuasiveness. Keep it concise (2-3 paragraphs)."""
                            
                            prompt = f"""Enhance this innovation idea:

Title: {title}
Description: {description}
Problem: {problem}
Solution: {solution}
Benefits: {benefits}

Provide an improved description that is professional, clear, and compelling."""
                            
                            enhanced = call_ai_api(prompt, system_prompt)
                            if enhanced:
                                final_description = enhanced
                                st.success("✅ AI enhanced your description!")
                    
                    # Create new idea
                    new_id = st.session_state.ideas_df['id'].max() + 1 if not st.session_state.ideas_df.empty else 1
                    
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
                        'cost_savings': 0,
                        'revenue_impact': 0
                    }
                    
                    st.session_state.ideas_df = pd.concat([
                        st.session_state.ideas_df,
                        pd.DataFrame([new_idea])
                    ], ignore_index=True)
                    
                    # Update user stats
                    user_idx = st.session_state.users_df[st.session_state.users_df['username'] == user['username']].index
                    st.session_state.users_df.loc[user_idx, 'ideas_submitted'] += 1
                    
                    # Award points
                    award_points(user['username'], 10, "submitting idea")
                    
                    st.success("🎉 Idea submitted successfully!")
                    st.balloons()
                    st.info("💡 Your idea will be reviewed by the innovation team. Check back for updates!")
    
    with tab4:
        st.title("📊 Innovation Analytics")
        
        # Time period selector
        period = st.selectbox(
            "📅 Time Period",
            ['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Last Year', 'All Time']
        )
        
        st.divider()
        
        # Submission trends
        st.subheader("📈 Submission Trends")
        ideas_df_copy = st.session_state.ideas_df.copy()
        ideas_df_copy['submit_date'] = pd.to_datetime(ideas_df_copy['submit_date'])
        ideas_by_month = ideas_df_copy.groupby(ideas_df_copy['submit_date'].dt.to_period('M')).size()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ideas_by_month.index.astype(str),
            y=ideas_by_month.values,
            mode='lines+markers',
            name='Ideas Submitted',
            line=dict(color='#667eea', width=3),
            marker=dict(size=10)
        ))
        fig.update_layout(
            title="Ideas Submitted Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Ideas",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Ideas by Department")
            dept_data = st.session_state.ideas_df.merge(
                st.session_state.users_df[['username', 'department']],
                left_on='submitter',
                right_on='username',
                how='left'
            )
            dept_counts = dept_data['department'].value_counts()
            
            fig = px.bar(
                x=dept_counts.values,
                y=dept_counts.index,
                orientation='h',
                color=dept_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=300,
                showlegend=False,
                xaxis_title="Number of Ideas",
                yaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("✅ Success Rate")
            total = len(st.session_state.ideas_df)
            approved = len(st.session_state.ideas_df[st.session_state.ideas_df['status'].isin(['Approved', 'In Progress', 'Implemented'])])
            rejected = len(st.session_state.ideas_df[st.session_state.ideas_df['status'] == 'Rejected'])
            pending = total - approved - rejected
            
            fig = go.Figure(data=[go.Pie(
                labels=['Approved/In Progress', 'Rejected', 'Pending Review'],
                values=[approved, rejected, pending],
                hole=0.4,
                marker=dict(colors=['#4caf50', '#f44336', '#ff9800'])
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Impact metrics
        st.subheader("💰 Business Impact")
        col1, col2, col3, col4 = st.columns(4)
        
        total_savings = st.session_state.ideas_df['cost_savings'].fillna(0).sum()
        total_revenue = st.session_state.ideas_df['revenue_impact'].fillna(0).sum()
        avg_score = st.session_state.ideas_df[st.session_state.ideas_df['total_score'] > 0]['total_score'].mean()
        
        col1.metric("💵 Cost Savings", f"${total_savings:,.0f}")
        col2.metric("📈 Revenue Impact", f"${total_revenue:,.0f}")
        col3.metric("🎯 Total Value", f"${total_savings + total_revenue:,.0f}")
        col4.metric("⭐ Avg Score", f"{avg_score:.1f}/40" if not pd.isna(avg_score) else "N/A")
    
    with tab5:
        st.title("🏆 Leaderboard")
        
        lead_tab1, lead_tab2, lead_tab3 = st.tabs(["👤 Top Contributors", "🏢 Departments", "💡 Top Ideas"])
        
        with lead_tab1:
            st.subheader("🌟 Top Innovators")
            
            rankings = st.session_state.users_df.sort_values('points', ascending=False).head(10)
            
            for idx, (i, row) in enumerate(rankings.iterrows()):
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
                
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
                    level, level_name, emoji = calculate_level(row['points'])
                    st.markdown(f"**{row['username']}**")
                    st.caption(f"{emoji} Level {level}: {level_name}")
                
                with col3:
                    st.metric("⭐ Points", int(row['points']))
                
                with col4:
                    st.metric("💡 Ideas", int(row['ideas_submitted']))
                
                with col5:
                    st.metric("✅ Approved", int(row['ideas_approved']))
                
                st.divider()
        
        with lead_tab2:
            st.subheader("🏢 Department Rankings")
            
            dept_data = st.session_state.ideas_df.merge(
                st.session_state.users_df[['username', 'department']],
                left_on='submitter',
                right_on='username',
                how='left'
            )
            
            dept_stats = dept_data.groupby('department').agg({
                'id': 'count',
                'upvotes': 'sum',
                'total_score': 'mean'
            }).round(2)
            
            dept_stats.columns = ['Total Ideas', 'Total Upvotes', 'Avg Score']
            dept_stats = dept_stats.sort_values('Total Ideas', ascending=False)
            
            st.dataframe(dept_stats, use_container_width=True)
        
        with lead_tab3:
            st.subheader("💡 Most Popular Ideas")
            
            top_ideas = st.session_state.ideas_df.sort_values('upvotes', ascending=False).head(10)
            
            for idx, row in top_ideas.iterrows():
                with st.expander(f"💡 {row['title']} - 👍 {row['upvotes']} upvotes"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Category:** {row['category']}")
                        st.write(f"**Submitted by:** {row['submitter']}")
                        st.write(row['description'])
                    with col2:
                        st.metric("Status", row['status'])
                        st.metric("Comments", row['comments_count'])
    
    with tab6:
        st.title("⚙️ Admin Dashboard")
        
        if user['role'] != 'Admin':
            st.warning("⚠️ This section is only accessible to administrators.")
            st.info("Please contact your system administrator for access.")
        else:
            st.success("👑 Administrator Access Granted")
            
            admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📋 Review Ideas", "👥 Manage Users", "📊 Reports"])
            
            with admin_tab1:
                st.subheader("💡 Ideas Pending Review")
                
                pending = st.session_state.ideas_df[st.session_state.ideas_df['status'].isin(['New', 'Under Review'])]
                
                if pending.empty:
                    st.info("🎉 No ideas pending review!")
                else:
                    for idx, row in pending.iterrows():
                        with st.expander(f"💡 {row['title']} - {row['status']}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Category:** {row['category']}")
                                st.write(f"**Submitted by:** {row['submitter']} on {row['submit_date']}")
                                st.write(f"**Description:** {row['description']}")
                                st.write(f"**Problem:** {row['problem']}")
                                st.write(f"**Solution:** {row['solution']}")
                                st.write(f"**Benefits:** {row['benefits']}")
                            
                            with col2:
                                st.metric("👍 Upvotes", row['upvotes'])
                                st.metric("💬 Comments", row['comments_count'])
                            
                            st.divider()
                            
                            # Evaluation form
                            with st.form(f"eval_form_{idx}"):
                                st.markdown("**📊 Evaluate Idea:**")
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    impact = st.slider("💥 Impact Score", 1, 10, 5, key=f"impact_{idx}")
                                    feasibility = st.slider("🔧 Feasibility Score", 1, 10, 5, key=f"feas_{idx}")
                                with col_b:
                                    innovation = st.slider("💡 Innovation Score", 1, 10, 5, key=f"innov_{idx}")
                                    strategic = st.slider("🎯 Strategic Alignment", 1, 10, 5, key=f"strat_{idx}")
                                
                                eval_comments = st.text_area("💬 Evaluation Comments", key=f"eval_comments_{idx}")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    if st.form_submit_button("✅ Approve", use_container_width=True):
                                        st.session_state.ideas_df.loc[idx, 'status'] = 'Approved'
                                        st.session_state.ideas_df.loc[idx, 'impact_score'] = impact
                                        st.session_state.ideas_df.loc[idx, 'feasibility_score'] = feasibility
                                        st.session_state.ideas_df.loc[idx, 'innovation_score'] = innovation
                                        st.session_state.ideas_df.loc[idx, 'strategic_score'] = strategic
                                        st.session_state.ideas_df.loc[idx, 'total_score'] = impact + feasibility + innovation + strategic
                                        
                                        # Update user stats
                                        submitter = row['submitter']
                                        user_idx = st.session_state.users_df[st.session_state.users_df['username'] == submitter].index
                                        st.session_state.users_df.loc[user_idx, 'ideas_approved'] += 1
                                        
                                        award_points(submitter, 100, "idea approved")
                                        st.success("✅ Idea approved!")
                                        st.rerun()
                                
                                with col2:
                                    if st.form_submit_button("🔄 Mark Under Review", use_container_width=True):
                                        st.session_state.ideas_df.loc[idx, 'status'] = 'Under Review'
                                        st.info("🔄 Status updated to Under Review")
                                        st.rerun()
                                
                                with col3:
                                    if st.form_submit_button("❌ Reject", use_container_width=True):
                                        st.session_state.ideas_df.loc[idx, 'status'] = 'Rejected'
                                        st.warning("❌ Idea rejected")
                                        st.rerun()
            
            with admin_tab2:
                st.subheader("👥 User Management")
                
                st.dataframe(
                    st.session_state.users_df[['username', 'email', 'department', 'role', 'points', 'level', 'ideas_submitted', 'ideas_approved']],
                    use_container_width=True
                )
                
                st.divider()
                
                st.subheader("➕ Add New User")
                with st.form("add_user_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_username = st.text_input("Username")
                        new_email = st.text_input("Email")
                        new_department = st.selectbox("Department", ['IT', 'Product', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations'])
                    with col2:
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Role", ['Employee', 'Admin'])
                    
                    if st.form_submit_button("➕ Add User"):
                        if new_username and new_password and new_email:
                            new_user = {
                                'username': new_username,
                                'password': hashlib.sha256(new_password.encode()).hexdigest(),
                                'email': new_email,
                                'department': new_department,
                                'role': new_role,
                                'join_date': datetime.now().strftime('%Y-%m-%d'),
                                'points': 0,
                                'level': 1,
                                'ideas_submitted': 0,
                                'ideas_approved': 0
                            }
                            st.session_state.users_df = pd.concat([
                                st.session_state.users_df,
                                pd.DataFrame([new_user])
                            ], ignore_index=True)
                            st.success(f"✅ User {new_username} added successfully!")
                            st.rerun()
                        else:
                            st.error("Please fill in all fields")
            
            with admin_tab3:
                st.subheader("📊 Generate Reports")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 Export All Ideas", use_container_width=True):
                        output = BytesIO()
                        st.session_state.ideas_df.to_excel(output, index=False, engine='openpyxl')
                        
                        st.download_button(
                            label="💾 Download Ideas Excel",
                            data=output.getvalue(),
                            file_name=f"ideas_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                with col2:
                    if st.button("📥 Export User Data", use_container_width=True):
                        output = BytesIO()
                        st.session_state.users_df.to_excel(output, index=False, engine='openpyxl')
                        
                        st.download_button(
                            label="💾 Download Users Excel",
                            data=output.getvalue(),
                            file_name=f"users_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                st.divider()
                
                st.subheader("📈 Executive Summary")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("👥 Total Users", len(st.session_state.users_df))
                col2.metric("💡 Total Ideas", len(st.session_state.ideas_df))
                col3.metric("📊 Avg Idea Score", f"{st.session_state.ideas_df[st.session_state.ideas_df['total_score'] > 0]['total_score'].mean():.1f}/40")
                
                st.markdown("""
                ### 📋 Key Metrics
                
                - **Participation Rate:** High engagement across departments
                - **Approval Rate:** Balanced review process
                - **Innovation Impact:** Significant cost savings and revenue growth
                - **User Engagement:** Active community with regular submissions
                """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p style='font-size: 1.2rem;'><strong>💡 Employee Idea Management System</strong></p>
    <p>Empowering Innovation • Driving Growth • Building Culture</p>
    <p style='font-size: 0.85rem; opacity: 0.8;'>
        Built with ❤️ using Streamlit • AI-Powered Features • Real-time Collaboration
    </p>
</div>
""", unsafe_allow_html=True)
