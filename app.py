import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import time
import db

# Initialize Database
db.init_db()

# --- Page Config ---
st.set_page_config(page_title="Intellektual Bellashuv", page_icon="🎓", layout="wide")

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
    
    /* LaTeX / Math styling */
    .katex-display {
        margin: 1em 0;
        overflow-x: auto;
        overflow-y: hidden;
    }
    
    /* Responsive design for mobile */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
            margin-bottom: 1rem !important;
        }
        .leaderboard-header {
            font-size: 1.5rem !important;
            margin-top: 1rem !important;
        }
        .stButton > button {
            height: 2.5rem !important;
            font-size: 0.9rem !important;
        }
        .streamlit-expanderHeader {
            font-size: 1rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Session Persistence Logic ---
def save_session(role, comp_id=None, student_id=None):
    st.query_params["role"] = role
    if comp_id: st.query_params["comp_id"] = str(comp_id)
    if student_id: st.query_params["student_id"] = str(student_id)

def clear_session():
    st.query_params.clear()
    for key in ["role", "comp_id", "student_id"]:
        if key in st.session_state:
            del st.session_state[key]

# --- Session State Initialization ---
if "role" not in st.session_state:
    # Try to restore from query params
    params = st.query_params
    if "role" in params:
        st.session_state["role"] = params["role"]
        if "comp_id" in params: st.session_state["comp_id"] = int(params["comp_id"])
        if "student_id" in params: st.session_state["student_id"] = int(params["student_id"])
    else:
        st.session_state["role"] = None

def get_time_left(comp):
    if not comp: return 0
    limit = comp['time_limit']
    start_time = comp['start_time']
    if not start_time:
        return limit
    elapsed = time.time() - start_time
    remaining = limit - elapsed
    return max(0, remaining)

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

# --- Pages ---

def super_admin_page():
    st.title("🔑 Asosiy Boshqaruv Paneli (Super Admin)")
    
    if st.button("⬅️ Chiqish"):
        clear_session()
        st.rerun()

    tab1, tab2 = st.tabs(["🎮 Musobaqalar", "➕ Yangi Musobaqa"])
    
    with tab1:
        comps = db.get_all_competitions()
        if not comps:
            st.info("Hozircha musobaqalar yo'q.")
        else:
            for c in comps:
                with st.expander(f"📍 {c['name']} (Kod: {c['code']}) - Holat: {c['status']}"):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**Admin Paroli:** `{c['admin_password']}`")
                    col1.write(f"**Vaqt Limiti:** {c['time_limit'] // 60} daqiqa")
                    
                    if col2.button("🗑️ O'chirish", key=f"del_comp_{c['id']}"):
                        db.delete_competition(c['id'])
                        st.success("Musobaqa o'chirildi!")
                        st.rerun()
                    
                    if col2.button("👁️ Admin panelga kirish", key=f"go_admin_{c['id']}"):
                        st.session_state["role"] = "admin"
                        st.session_state["comp_id"] = c['id']
                        save_session("admin", comp_id=c['id'])
                        st.rerun()

    with tab2:
        with st.form("new_comp_form"):
            name = st.text_input("Musobaqa nomi (masalan: Matematika 9-sinf)")
            code = st.text_input("4 xonali kod", max_chars=4)
            admin_pass = st.text_input("Admin paroli")
            time_limit = st.number_input("Vaqt limiti (daqiqa)", min_value=1, value=30)
            
            if st.form_submit_button("Yaratish"):
                if name and code and admin_pass:
                    if len(code) != 4:
                        st.error("Kod 4 xonali bo'lishi kerak!")
                    else:
                        res = db.create_competition(name, code, admin_pass, time_limit)
                        if res:
                            st.success(f"Musobaqa yaratildi! Kod: {code}")
                            st.rerun()
                        else:
                            st.error("Bu kod band yoki xato yuz berdi.")
                else:
                    st.error("Barcha maydonlarni to'ldiring!")

def login_page():
    st.markdown("<h1 class='main-header'>Intellektual Bellashuv Platformasi</h1>", unsafe_allow_html=True)
    
    if "temp_comp" not in st.session_state:
        st.session_state["temp_comp"] = None

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state["temp_comp"]:
            st.subheader("Musobaqa kodini kiriting")
            comp_code = st.text_input("Imtihon kodi (4 xonali)", max_chars=4)
            if st.button("Davom etish"):
                if comp_code == "7777": # Hardcoded Super Admin code
                    st.session_state["role"] = "super_admin"
                    save_session("super_admin")
                    st.rerun()
                
                comp = db.get_competition_by_code(comp_code)
                if comp:
                    st.session_state["temp_comp"] = comp
                    st.rerun()
                else:
                    st.error("Noto'g'ri kod!")
        else:
            comp = st.session_state["temp_comp"]
            st.info(f"Musobaqa: **{comp['name']}**")
            
            tab1, tab2 = st.tabs(["🎓 O'quvchi", "🛡️ Admin"])
            
            with tab1:
                st.subheader("O'quvchi kirishi")
                f_name = st.text_input("Ism")
                l_name = st.text_input("Familiya")
                pwd = st.text_input("Parol", type="password", help="Yangi bo'lsangiz, parol o'ylab toping. Eski bo'lsangiz, o'sha parolni yozing.")
                
                if st.button("Kirish"):
                    if f_name and l_name and pwd:
                        # Check if student exists
                        student = db.get_student_by_login(comp['id'], f_name, l_name, pwd)
                        if student:
                            st.session_state["role"] = "student"
                            st.session_state["student_id"] = student['id']
                            st.session_state["comp_id"] = comp['id']
                            save_session("student", comp_id=comp['id'], student_id=student['id'])
                            st.rerun()
                        else:
                            # Try to register
                            try:
                                student_id = db.add_student(comp['id'], f_name, l_name, pwd)
                                st.session_state["role"] = "student"
                                st.session_state["student_id"] = student_id
                                st.session_state["comp_id"] = comp['id']
                                save_session("student", comp_id=comp['id'], student_id=student_id)
                                st.rerun()
                            except:
                                st.error("Xato yuz berdi. Balki parol noto'g'ridir?")
                    else:
                        st.error("Ma'lumotlarni to'ldiring!")
            
            with tab2:
                st.subheader("Admin kirishi")
                admin_pwd = st.text_input("Admin paroli", type="password")
                if st.button("Adminga kirish"):
                    if admin_pwd == comp['admin_password']:
                        st.session_state["role"] = "admin"
                        st.session_state["comp_id"] = comp['id']
                        save_session("admin", comp_id=comp['id'])
                        st.rerun()
                    else:
                        st.error("Noto'g'ri parol!")
            
            if st.button("⬅️ Orqaga"):
                st.session_state["temp_comp"] = None
                st.rerun()

def admin_page():
    comp_id = st.session_state.get("comp_id")
    comp = db.get_competition_by_id(comp_id)
    if not comp:
        clear_session()
        st.rerun()

    st_autorefresh(interval=3000, key="admin_refresh")
    st.title(f"🛡️ Admin: {comp['name']}")
    
    tab1, tab2 = st.tabs(["📊 Jonli Reyting", "📝 Savollar"])
    
    questions_db = db.get_all_questions(comp_id)
    total_q = len(questions_db)
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("<h3 class='leaderboard-header'>Jonli Reyting</h3>", unsafe_allow_html=True)
            students = db.get_all_students(comp_id)
            if students:
                df = pd.DataFrame(students)
                df['Progress'] = df['solved_questions'].apply(lambda x: len(x))
                ranks = []
                for i in range(len(df)):
                    rank = i + 1
                    if rank == 1: ranks.append("👑 1")
                    elif rank == 2: ranks.append("👑 2")
                    elif rank == 3: ranks.append("👑 3")
                    else: ranks.append(str(rank))
                df["O'rin"] = ranks
                df = df[["O'rin", 'first_name', 'last_name', 'score', 'Progress']]
                df.columns = ["O'rin", "Ism", "Familiya", "Ball", "Natija"]
                df["Natija"] = df["Natija"].apply(lambda x: f"{x}/{total_q}")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Hali hech kim kirmadi.")
                
        with col2:
            st.subheader("Boshqaruv")
            status = comp['status']
            
            if status == 'pending':
                if st.button("🟢 Musobaqani boshlash"):
                    db.update_competition_status(comp_id, 'started', start_time=time.time())
                    st.rerun()
            elif status == 'started':
                time_left = get_time_left(comp)
                if time_left > 0:
                    st.success("Musobaqa qizg'in pallada.")
                    st.metric("Qolgan vaqt", format_time(time_left))
                    if st.button("🛑 To'xtatish"):
                        db.update_competition_status(comp_id, 'finished')
                        st.rerun()
                else:
                    db.update_competition_status(comp_id, 'finished')
                    st.rerun()
            else:
                st.error("Musobaqa tugadi.")
                if st.button("🔄 Qayta boshlash (Natijalarni o'chirish)"):
                    db.reset_scores(comp_id)
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Tizimdan chiqish"):
                clear_session()
                st.rerun()

    with tab2:
        st.subheader("Savollar")
        for idx, q in enumerate(questions_db):
            with st.container():
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{idx+1}. {q['topic']}** (Ball: {q['score']})")
                c1.markdown(f"{q['question']}")
                if c2.button("🗑️", key=f"del_{q['id']}"):
                    db.delete_question(q['id'])
                    st.rerun()
            st.markdown("---")
        
        with st.expander("➕ Yangi savol qo'shish"):
            with st.form("add_q"):
                t = st.text_input("Mavzu")
                q_text = st.text_area("Savol")
                a = st.text_input("Javob")
                s = st.number_input("Ball", min_value=1, value=10)
                if st.form_submit_button("Saqlash"):
                    if t and q_text and a:
                        db.add_question(comp_id, t, q_text, a, s)
                        st.rerun()

def student_page():
    student_id = st.session_state.get("student_id")
    comp_id = st.session_state.get("comp_id")
    student = db.get_student(student_id)
    comp = db.get_competition_by_id(comp_id)
    
    if not student or not comp:
        clear_session()
        st.rerun()
        
    solved = student.get("solved_questions", [])
    questions_db = db.get_all_questions(comp_id)
    total_q = len(questions_db)
    
    st.sidebar.title(f"👤 {student['first_name']} {student['last_name']}")
    st.sidebar.metric("Ballingiz", student["score"])
    st.sidebar.write(f"Natija: {len(solved)}/{total_q}")
    
    if comp['status'] == 'started':
        time_left = get_time_left(comp)
        if time_left > 0:
            st.sidebar.metric("⏳ Qolgan vaqt", format_time(time_left))
            st_autorefresh(interval=5000, key="st_active")
            
            st.markdown("## Savollar")
            for idx, q in enumerate(questions_db):
                q_id = q['id']
                is_solved = q_id in solved
                icon = "✅" if is_solved else "📝"
                with st.expander(f"{icon} {idx+1}-savol"):
                    st.markdown(q["question"])
                    if is_solved:
                        st.success(f"To'g'ri! (+{q['score']} ball)")
                    else:
                        with st.form(key=f"f_{q_id}"):
                            ans = st.text_input("Javob:")
                            if st.form_submit_button("Tekshirish"):
                                user_ans = ans.replace(" ", "").replace(",", ".").lower()
                                correct = [a.replace(" ", "").replace(",", ".").lower() for a in str(q["answer"]).split("|")]
                                if user_ans in correct:
                                    st.balloons()
                                    new_score = student["score"] + q['score']
                                    solved.append(q_id)
                                    db.update_score(student_id, new_score, solved)
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Xato!")
        else:
            st.error("Vaqt tugadi!")
    elif comp['status'] == 'finished':
        st.header("🏁 Musobaqa yakunlandi")
        st.write(f"Sizning yakuniy ballingiz: **{student['score']}**")
        
        # Show Leaderboard
        students = db.get_all_students(comp_id)
        df = pd.DataFrame(students)
        df['Natija'] = df['solved_questions'].apply(lambda x: f"{len(x)}/{total_q}")
        df = df[["first_name", "last_name", "score", "Natija"]]
        df.columns = ["Ism", "Familiya", "Ball", "Natija"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st_autorefresh(interval=3000, key="st_wait")
        st.info("⏳ Musobaqa boshlanishini kuting...")

    if st.sidebar.button("Chiqish"):
        clear_session()
        st.rerun()

# --- Main Logic ---
role = st.session_state.get("role")
if role == "super_admin":
    super_admin_page()
elif role == "admin":
    admin_page()
elif role == "student":
    student_page()
else:
    login_page()
