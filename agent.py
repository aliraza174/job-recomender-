import streamlit as st
from pyswip import Prolog
from thefuzz import fuzz
from textblob import TextBlob
import re
from sentence_transformers import SentenceTransformer, util
import torch

# Load Prolog knowledge base
prolog = Prolog()
prolog.consult("Prolog.pl")

# Load sentence transformer model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Synonym mapping
synonyms = {
    "developer": "software engineer",
    "programmer": "software engineer",
    "coder": "software engineer",
    "web dev": "web developer",
    "bsc": "bachelors",
    "msc": "masters"
}

# Helper functions
def normalize_term(term):
    return synonyms.get(term.lower(), term.lower())

def parse_salary(user_input):
    numbers = re.findall(r"\d+", user_input.replace(",", ""))
    return int(numbers[0]) if numbers else None

def correct_text(text):
    return str(TextBlob(text).correct())

def safe_markdown(text):
    safe_content = text.encode("utf-8", "ignore").decode("utf-8")
    st.markdown(safe_content)

def get_all_jobs():
    return list(prolog.query("job(JobID, Title, Field, Skills, Qualification, City, Salary)"))

intent_phrases = {
    "exit": [
        "bye", "goodbye", "exit", "leave", "see you", "quit", "close the app", "stop talking", "end chat",
        "farewell", "talk later", "I am done", "log out"
    ],
    
    "qualify": [
        "find jobs for me", "am I qualified?", "get matched", "qualify", "which job for me",
        "which job suits me", "recommend jobs", "suggest job options", "what jobs can I get",
        "check my eligibility", "which positions I can apply for", "possible jobs for me",
        "show suitable roles", "jobs based on my skills", "find me a job"
    ],
    
    "see_jobs": [
        "show me jobs", "list all jobs", "available positions", "see jobs",
        "show current vacancies", "open job listings", "job opportunities", "vacant positions",
        "job openings", "display jobs", "jobs available now", "hiring positions",
        "what jobs do you have", "available job roles", "jobs on offer"
    ],
    
    "show_detail": [
        "job details", "more info", "show job", "job detail", "show detail",
        "job description", "tell me about this job", "describe the job", "what are the job requirements",
        "what is the job about", "job info", "see job responsibilities", "job specifications",
        "can you explain this job", "full job details"
    ]
}



def classify_with_embeddings(user_text):
    user_embedding = embedder.encode(user_text, convert_to_tensor=True)
    best_intent = "unknown"
    best_score = 0.0
    for intent, phrases in intent_phrases.items():
        phrase_embeddings = embedder.encode(phrases, convert_to_tensor=True)
        similarity = util.cos_sim(user_embedding, phrase_embeddings).max().item()
        if similarity > best_score and similarity > 0.65:
            best_intent = intent
            best_score = similarity
    return best_intent

# Skill matching using embeddings
def get_skill_match_score(user_skills, job_skills):
    if not job_skills or not user_skills:
        return 0.0
    job_skill_embeddings = embedder.encode(job_skills, convert_to_tensor=True)
    user_skill_embeddings = embedder.encode(user_skills, convert_to_tensor=True)
    sim_matrix = util.cos_sim(user_skill_embeddings, job_skill_embeddings)
    avg_sim = sim_matrix.max(dim=1).values.mean().item()
    return avg_sim

# Job matcher function using embeddings
def get_job_matches(qualification, skills, fields, min_salary):
    job_scores = []
    for result in get_all_jobs():
        salary_val = result.get("Salary")
        try:
            salary_num = int(salary_val)
            if min_salary is not None and salary_num < min_salary:
                continue
        except (ValueError, TypeError):
            pass

        score = 0
        total = 3

        if qualification:
            q_sim = util.cos_sim(
                embedder.encode(qualification, convert_to_tensor=True),
                embedder.encode(result.get("Qualification"), convert_to_tensor=True)
            ).item()
            if q_sim >= 0.7:
                score += 1

        job_skills = result.get("Skills", [])
        skill_score = get_skill_match_score(skills, job_skills)
        score += skill_score

        if fields:
            field_similarities = []
            for field in fields:
                f_sim = util.cos_sim(
                    embedder.encode(field, convert_to_tensor=True),
                    embedder.encode(result.get("Field"), convert_to_tensor=True)
                ).item()
                field_similarities.append(f_sim)
            if field_similarities and max(field_similarities) >= 0.7:
                score += 1

        percentage = round((score / total) * 100, 1)
        job_scores.append((result, percentage))

    job_scores.sort(key=lambda x: x[1], reverse=True)
    return job_scores

# ===========================
# 📌 Display App Heading
st.markdown(
    "<h1 style='text-align: center; color: #00FFCC; font-size: 50px; margin-bottom: 30px;'>🤖 Mr. Intelligent</h1>",
    unsafe_allow_html=True
)
# ===========================

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.stage = "start"
    st.session_state.user_data = {}
    st.session_state.matches = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hello! How can I help you today?\n\n- See all available jobs\n- Find out which jobs you qualify for"
    })

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        safe_markdown(message["content"])

# Input prompt
user_input = st.chat_input("Type your message here...")

if user_input:
    corrected = correct_text(user_input)
    st.session_state.messages.append({"role": "user", "content": corrected})
    text = corrected.lower()

    intent = classify_with_embeddings(corrected)

    if intent == "exit":
        st.session_state.messages.append({"role": "assistant", "content": "👋 Goodbye!"})
        st.rerun()

    if st.session_state.stage in ["start", "choice"]:
        if intent == "see_jobs":
            jobs = get_all_jobs()
            reply = "**📄 Available Jobs:**"
            for job in jobs:
                reply += (
                    f"\n\n---\n"
                    f"**Title:** {job['Title']}\n"
                    f"**Field:** {job['Field']}\n"
                    f"**Skills:** {', '.join(job['Skills'])}\n"
                    f"**Qualification:** {job['Qualification']}\n"
                    f"**City:** {job['City']}\n"
                    f"**Salary:** {job['Salary']}"
                )
            st.session_state.stage = "choice"
        elif intent == "qualify":
            st.session_state.stage = "ask_qualification"
            reply = "What's your qualification? (bachelors/masters or 'none')"
        else:
            reply = "Please type 'see jobs' or 'qualify'."
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.stage == "ask_qualification":
        st.session_state.user_data['qualification'] = None if text == "none" else normalize_term(text)
        st.session_state.stage = "ask_skills"
        st.session_state.messages.append({"role": "assistant", "content": "What skills do you have? (comma separated or 'none')"})
        st.rerun()

    if st.session_state.stage == "ask_skills":
        st.session_state.user_data['skills'] = [] if text == "none" else [normalize_term(s.strip()) for s in text.split(",") if s.strip()]
        st.session_state.stage = "ask_fields"
        st.session_state.messages.append({"role": "assistant", "content": "Which fields interest you? (comma separated or 'none')"})
        st.rerun()

    if st.session_state.stage == "ask_fields":
        st.session_state.user_data['fields'] = [] if text == "none" else [normalize_term(f.strip()) for f in text.split(",") if f.strip()]
        st.session_state.stage = "ask_salary"
        st.session_state.messages.append({"role": "assistant", "content": "What's your minimum salary expectation? (number or 'skip')"})
        st.rerun()

    if st.session_state.stage == "ask_salary":
        min_salary = 0 if "skip" in text else parse_salary(text)
        data = st.session_state.user_data
        matches = get_job_matches(data.get('qualification'), data.get('skills'), data.get('fields'), min_salary)
        st.session_state.matches = matches

        if matches:
            reply = "**📊 Your top job matches:**"
            for job, perc in matches:
                reply += f"\n\n- **{job['Title']}** ({perc}% match)"
            reply += "\n\nWould you like to see details for the top job?"
        else:
            reply = "No suitable jobs found."

        st.session_state.stage = "after_matches"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.stage == "after_matches" and intent == "show_detail":
        if st.session_state.matches:
            top_job = st.session_state.matches[0][0]
            reply = (
                "**📌 Top Job Detail:**\n\n"
                f"- **Title:** {top_job['Title']}\n"
                f"- **Field:** {top_job['Field']}\n"
                f"- **Skills:** {', '.join(top_job['Skills'])}\n"
                f"- **Qualification:** {top_job['Qualification']}\n"
                f"- **City:** {top_job['City']}\n"
                f"- **Salary:** {top_job['Salary']}"
            )
        else:
            reply = "No top job available to show."
        st.session_state.stage = "choice"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
