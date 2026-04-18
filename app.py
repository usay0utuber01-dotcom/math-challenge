import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import time
import db

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
    
    /* LaTeX / Math styling */
    .katex-display {
        margin: 1em 0;
        overflow-x: auto;
        overflow-y: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "role" not in st.session_state:
    st.session_state["role"] = None  # 'admin' or 'student'
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None

def get_time_left():
    limit = db.get_competition_time_limit()
    start_time = db.get_competition_start_time()
    if not start_time:
        return limit
    elapsed = time.time() - start_time
    remaining = limit - elapsed
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
    
    tab1, tab2 = st.tabs(["📊 Jonli Reyting va Boshqaruv", "📝 Savollarni Boshqarish"])
    
    questions_db = db.get_all_questions()
    total_q = len(questions_db)
    
    with tab1:
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
                # Convert progress to "X/total_q"
                df["Natija"] = df["Natija"].apply(lambda x: f"{x}/{total_q}")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # CSV Export
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Natijalarni yuklab olish (CSV)",
                    data=csv,
                    file_name='natijalar.csv',
                    mime='text/csv',
                )
            else:
                st.info("Hali hech kim kirmadi.")
                
        with col2:
            st.subheader("Boshqaruv")
            
            is_started = db.is_competition_started()
            
            # Time limit setting
            current_limit_minutes = db.get_competition_time_limit() // 60
            new_limit = st.number_input("⏳ O'yin vaqti (daqiqa):", min_value=1, max_value=300, value=current_limit_minutes, disabled=is_started)
            
            if new_limit != current_limit_minutes and not is_started:
                db.set_competition_time_limit(new_limit * 60)
                st.success("Vaqt o'zgartirildi!")
                time.sleep(0.5)
                st.rerun()
                
            if not is_started:
                st.warning("Musobaqa to'xtatilgan/kutilmoqda.")
                if st.button("🟢 Musobaqani boshlash"):
                    db.set_competition_started(True)
                    st.rerun()
            else:
                time_left = get_time_left()
                if time_left > 0:
                    st.success("Musobaqa qizg'in pallada.")
                    import streamlit.components.v1 as components
                    html_code = f"""
                    <div style="font-family: sans-serif; padding: 10px; background: #262730; color: white; border-radius: 8px; text-align: center; font-size: 1.2rem; font-weight: bold; border: 1px solid #38bdf8;">
                        ⏳ <span id="admin_clock">{format_time(time_left)}</span>
                    </div>
                    <script>
                    var timeLeft = {int(time_left)};
                    var clock = document.getElementById('admin_clock');
                    var timerId = setInterval(function() {{
                        timeLeft--;
                        if (timeLeft <= 0) {{
                            clearInterval(timerId);
                            clock.innerHTML = "Vaqt tugadi!";
                            clock.style.color = "#ef4444";
                            window.parent.location.reload();
                        }} else {{
                            var m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                            var s = Math.floor(timeLeft % 60).toString().padStart(2, '0');
                            clock.innerHTML = m + ":" + s;
                        }}
                    }}, 1000);
                    </script>
                    """
                    components.html(html_code, height=60)
                else:
                    st.error("Musobaqa vaqti tugadi.")
                    
                if st.button("🛑 To'xtatish"):
                    db.set_competition_started(False)
                    st.rerun()
                    
            st.markdown("---")
            if st.button("🔄 Natijalarni nollash (O'quvchilar qoladi)"):
                st.session_state['confirm_reset_scores'] = True
                
            if st.session_state.get('confirm_reset_scores', False):
                st.warning("Barcha natijalar va vaqt nollanadi. Davom etamizmi?")
                c1, c2 = st.columns(2)
                if c1.button("Ha, nollash", key="btn_yes_scores"):
                    db.reset_scores()
                    st.session_state['confirm_reset_scores'] = False
                    st.rerun()
                if c2.button("Bekor qilish", key="btn_no_scores"):
                    st.session_state['confirm_reset_scores'] = False
                    st.rerun()
                    
            if st.button("⚠️ Barcha o'quvchilarni o'chirish"):
                st.session_state['confirm_reset'] = True
                
            if st.session_state.get('confirm_reset', False):
                st.warning("Haqiqatan ham hamma o'quvchilarni tizimdan o'chirmoqchimisiz?")
                c1, c2 = st.columns(2)
                if c1.button("Ha, o'chirish", key="btn_yes_all"):
                    db.reset_db()
                    st.session_state['confirm_reset'] = False
                    st.rerun()
                if c2.button("Bekor qilish", key="btn_no_all"):
                    st.session_state['confirm_reset'] = False
                    st.rerun()
                
            st.markdown("---")
            if st.button("Tizimdan chiqish"):
                st.session_state["role"] = None
                st.rerun()

    with tab2:
        st.subheader("Barcha savollar")
        
        if not questions_db:
            st.info("Hozircha savollar yo'q.")
        
        for idx, q in enumerate(questions_db):
            with st.container():
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{idx+1}. {q['topic']}** (Ball: {q['score']})")
                c1.markdown(f"{q['question']}")
                c1.markdown(f"*Javoblar:* `{q['answer']}`")
                
                if c2.button("🗑️ O'chirish", key=f"del_{q['id']}"):
                    db.delete_question(q['id'])
                    st.success("Savol o'chirildi!")
                    st.rerun()
            st.markdown("---")
            
        with st.expander("➕ Yangi savol qo'shish", expanded=False):
            with st.form("add_question_form"):
                new_topic = st.text_input("Mavzu")
                new_q = st.text_area("Savol matni (Matematik formulalarni $ $ belgisi ichiga yozishingiz mumkin)")
                new_ans = st.text_input("To'g'ri javob (bir nechta variant bo'lsa | bilan ajrating)")
                new_score = st.number_input("Ball", min_value=1, value=10)
                
                if st.form_submit_button("Qo'shish"):
                    if new_topic and new_q and new_ans:
                        db.add_question(new_topic, new_q, new_ans, new_score)
                        st.success("Yangi savol qo'shildi!")
                        st.rerun()
                    else:
                        st.error("Barcha maydonlarni to'ldiring!")

def student_page():
    student_id = st.session_state["student_id"]
    student = db.get_student(student_id)
    
    if not student:
        st.session_state["role"] = None
        st.rerun()
        
    is_started = db.is_competition_started()
    solved = student.get("solved_questions", [])
    
    questions_db = db.get_all_questions()
    total_q = len(questions_db)
    
    # Calculate rank
    students = db.get_all_students()
    my_rank = "-"
    for i, s in enumerate(students):
        if s['id'] == student_id:
            my_rank = i + 1
            break
            
    rank_str = f"👑 {my_rank}" if my_rank in [1, 2, 3] else str(my_rank)
    
    st.sidebar.title(f"👤 {student['first_name']} {student['last_name']}")
    st.sidebar.markdown(f"### 🏆 O'rningiz: {rank_str}")
    st.sidebar.metric("Sizning ballingiz", student["score"])
    
    progress_val = len(solved) / total_q if total_q > 0 else 0
    st.sidebar.progress(progress_val)
    st.sidebar.write(f"Natija: {len(solved)}/{total_q}")
    
    if is_started:
        time_left = get_time_left()
        st.sidebar.markdown("---")
        if time_left > 0:
            import streamlit.components.v1 as components
            html_code = f"""
            <div style="font-family: sans-serif; padding: 10px; background: #262730; color: white; border-radius: 8px; text-align: center; font-size: 1.2rem; font-weight: bold; border: 1px solid #38bdf8;">
                ⏳ <span id="clock">{format_time(time_left)}</span>
            </div>
            <script>
            var timeLeft = {int(time_left)};
            var clock = document.getElementById('clock');
            var timerId = setInterval(function() {{
                timeLeft--;
                if (timeLeft <= 0) {{
                    clearInterval(timerId);
                    clock.innerHTML = "Vaqt tugadi!";
                    clock.style.color = "#ef4444";
                    // Reload parent page to trigger Streamlit's time up screen
                    window.parent.location.reload();
                }} else {{
                    var m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                    var s = Math.floor(timeLeft % 60).toString().padStart(2, '0');
                    clock.innerHTML = m + ":" + s;
                }}
            }}, 1000);
            </script>
            """
            st.sidebar.markdown("---")
            with st.sidebar:
                components.html(html_code, height=60)
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
            if len(solved) == total_q and total_q > 0:
                st.balloons()
                st.markdown("<h2 style='text-align: center; color: #10B981;'>🏆 Barcha savollarni yakunladingiz!</h2>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align: center; color: #EF4444;'>⏰ Vaqt tugadi!</h2>", unsafe_allow_html=True)
            st.write(f"### Yakuniy ballingiz: {student['score']}")
            
            st.markdown("---")
            st.markdown("<h3 class='leaderboard-header'>Jonli Reyting</h3>", unsafe_allow_html=True)
            
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
                df["Natija"] = df["Natija"].apply(lambda x: f"{x}/{total_q}")
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            # Show all questions
            st.markdown("## Savollar", unsafe_allow_html=True)
            st.info("💡 Istalgan savoldan boshlashingiz mumkin. Xato javob uchun ball olinmaydi, qayta urinib ko'rish cheklanmagan.")
            
            for idx, q in enumerate(questions_db):
                q_id = q['id']
                is_solved = q_id in solved
                icon = "✅" if is_solved else "📝"
                
                with st.expander(f"{icon} {idx+1}-savol", expanded=False):
                    st.markdown(f"**Mavzu:** {q['topic']} (Ball: {q['score']})")
                    # Using st.markdown allows LaTeX rendering if wrapped in $
                    st.markdown(q["question"])
                    
                    if is_solved:
                        st.success(f"Siz bu savolga to'g'ri javob bergansiz! 🎉 (+{q['score']} ball)")
                    else:
                        with st.form(key=f"q_form_{q_id}"):
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
                                        st.success(f"To'g'ri! 🎉 +{q['score']} ball")
                                        new_score = student["score"] + q['score']
                                        solved.append(q_id)
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
