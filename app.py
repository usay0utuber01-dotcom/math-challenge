import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import time
import db
from questions import QUESTIONS

# Initialize Database
db.init_db()

# --- Page Config ---
st.set_page_config(page_title="Math Challenge", page_icon="🧮", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    /* Beautiful colorful buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        color: white;
        border: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4);
        color: white;
        border: none;
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .leaderboard-header {
        color: #38BDF8;
        margin-top: 2rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "role" not in st.session_state:
    st.session_state["role"] = None  # 'admin' or 'student'
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None

TOTAL_TIME_SECONDS = 30 * 60  # 30 minutes

def get_time_left():
    start_time = db.get_competition_start_time()
    if not start_time:
        return TOTAL_TIME_SECONDS
    elapsed = time.time() - start_time
    remaining = TOTAL_TIME_SECONDS - elapsed
    return max(0, remaining)

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

# --- Routing ---
def login_page():
    st.markdown("<h1 class='main-header'>Math Challenge Platform</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🎓 O'quvchi", "🛡️ Admin"])
        
        with tab1:
            st.subheader("Musobaqaga qo'shilish")
            first_name = st.text_input("Ism")
            last_name = st.text_input("Familiya")
            if st.button("Kirish"):
                if first_name and last_name:
                    student_id = db.add_student(first_name, last_name)
                    st.session_state["role"] = "student"
                    st.session_state["student_id"] = student_id
                    st.rerun()
                else:
                    st.error("Iltimos ism va familiyangizni to'liq kiriting.")
                    
        with tab2:
            st.subheader("Admin paneli")
            password = st.text_input("Parol", type="password")
            if st.button("Adminga kirish"):
                if password == "admin123":
                    st.session_state["role"] = "admin"
                    st.rerun()
                else:
                    st.error("Noto'g'ri parol.")

def admin_page():
    # Auto-refresh every 3 seconds to keep leaderboard updated
    st_autorefresh(interval=3000, key="admin_refresh")
    
    st.title("🛡️ Admin Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<h3 class='leaderboard-header'>Jonli Reyting</h3>", unsafe_allow_html=True)
        students = db.get_all_students()
        if students:
            df = pd.DataFrame(students)
            df['Progress'] = df['solved_questions'].apply(lambda x: len(x))
            
            ranks = []
            for i in range(len(df)):
                rank = i + 1
                if rank == 1:
                    ranks.append("👑 1")
                elif rank == 2:
                    ranks.append("👑 2")
                elif rank == 3:
                    ranks.append("👑 3")
                else:
                    ranks.append(str(rank))
            df["O'rin"] = ranks
            
            df = df[["O'rin", 'first_name', 'last_name', 'score', 'Progress']]
            df.columns = ["O'rin", "Ism", "Familiya", "Ball", "Natija"]
            # Convert progress to "X/20"
            df["Natija"] = df["Natija"].apply(lambda x: f"{x}/{len(QUESTIONS)}")
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Hali hech kim kirmadi.")
            
    with col2:
        st.subheader("Boshqaruv")
        is_started = db.is_competition_started()
        
        if not is_started:
            st.warning("Musobaqa to'xtatilgan/kutilmoqda.")
            if st.button("🟢 Musobaqani boshlash"):
                db.set_competition_started(True)
                st.rerun()
        else:
            time_left = get_time_left()
            if time_left > 0:
                st.success("Musobaqa qizg'in pallada.")
                st.metric("Qolgan vaqt", format_time(time_left))
            else:
                st.error("Musobaqa vaqti tugadi.")
                
            if st.button("🛑 To'xtatish"):
                db.set_competition_started(False)
                st.rerun()
                
        st.markdown("---")
        if st.button("⚠️ Bazani tozalash (Restart)"):
            db.reset_db()
            st.rerun()
            
        if st.button("Tizimdan chiqish"):
            st.session_state["role"] = None
            st.rerun()

def student_page():
    student_id = st.session_state["student_id"]
    student = db.get_student(student_id)
    
    if not student:
        st.session_state["role"] = None
        st.rerun()
        
    is_started = db.is_competition_started()
    solved = student.get("solved_questions", [])
    
    st.sidebar.title(f"👤 {student['first_name']} {student['last_name']}")
    st.sidebar.metric("Sizning ballingiz", student["score"])
    st.sidebar.progress(len(solved) / len(QUESTIONS))
    st.sidebar.write(f"Natija: {len(solved)}/{len(QUESTIONS)}")
    
    if is_started:
        time_left = get_time_left()
        st.sidebar.markdown("---")
        if time_left > 0:
            st.sidebar.metric("⏳ Qolgan vaqt", format_time(time_left))
            # Refresh every 10 seconds for timer updates if active
            st_autorefresh(interval=10000, key="student_timer_refresh")
        else:
            st.sidebar.error("Vaqt tugadi!")
    
    if st.sidebar.button("Chiqish"):
        st.session_state["role"] = None
        st.rerun()
        
    if not is_started:
        # Waiting room
        st_autorefresh(interval=2000, key="student_waiting_refresh")
        st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>⏳ Musobaqa boshlanishini kuting...</h2>", unsafe_allow_html=True)
        st.info("Tayyor turing! Admin musobaqani boshlaganidan so'ng savollar ekranda paydo bo'ladi.")
    else:
        time_left = get_time_left()
        
        if time_left <= 0:
            # Completed / Time up
            st_autorefresh(interval=5000, key="student_completed_refresh")
            if len(solved) == len(QUESTIONS):
                st.balloons()
                st.markdown("<h2 style='text-align: center; color: #10B981;'>🏆 Barcha savollarni yakunladingiz!</h2>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align: center; color: #EF4444;'>⏰ Vaqt tugadi!</h2>", unsafe_allow_html=True)
            st.write(f"### Yakuniy ballingiz: {student['score']}")
            
            st.markdown("---")
            st.markdown("<h3 class='leaderboard-header'>Jonli Reyting</h3>", unsafe_allow_html=True)
            
            students = db.get_all_students()
            if students:
                df = pd.DataFrame(students)
                df['Progress'] = df['solved_questions'].apply(lambda x: len(x))
                
                ranks = []
                for i in range(len(df)):
                    rank = i + 1
                    if rank == 1:
                        ranks.append("👑 1")
                    elif rank == 2:
                        ranks.append("👑 2")
                    elif rank == 3:
                        ranks.append("👑 3")
                    else:
                        ranks.append(str(rank))
                df["O'rin"] = ranks
                
                df = df[["O'rin", 'first_name', 'last_name', 'score', 'Progress']]
                df.columns = ["O'rin", "Ism", "Familiya", "Ball", "Natija"]
                df["Natija"] = df["Natija"].apply(lambda x: f"{x}/{len(QUESTIONS)}")
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            # Show all questions
            st.markdown("## Savollar", unsafe_allow_html=True)
            st.info("💡 Istalgan savoldan boshlashingiz mumkin. Xato javob uchun ball olinmaydi, qayta urinib ko'rish cheklanmagan.")
            
            for i, q in enumerate(QUESTIONS):
                is_solved = i in solved
                icon = "✅" if is_solved else "📝"
                
                with st.expander(f"{icon} {i+1}-savol", expanded=False):
                    st.markdown(f"**Mavzu:** {q['topic']}")
                    st.write(q["question"])
                    
                    if is_solved:
                        st.success("Siz bu savolga to'g'ri javob bergansiz! 🎉")
                    else:
                        with st.form(key=f"q_form_{i}"):
                            choice = st.text_input("Javobingizni kiriting:")
                            submitted = st.form_submit_button("Javobni tekshirish")
                            
                            if submitted:
                                if not choice.strip():
                                    st.warning("Iltimos, avval javobingizni kiriting.")
                                else:
                                    user_ans = choice.replace(" ", "").replace(",", ".").lower()
                                    correct_answers = [ans.replace(" ", "").replace(",", ".").lower() for ans in str(q["answer"]).split("|")]
                                    
                                    if user_ans in correct_answers:
                                        st.balloons()
                                        st.success("To'g'ri! 🎉 +10 ball")
                                        new_score = student["score"] + 10
                                        solved.append(i)
                                        db.update_score(student_id, new_score, solved)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"Xato. Qayta urinib ko'ring! ❌")

# --- Main App Logic ---
role = st.session_state.get("role")

if role == "admin":
    admin_page()
elif role == "student":
    student_page()
else:
    login_page()
