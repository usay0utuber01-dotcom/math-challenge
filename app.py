import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import time
import json
import db
import math

# Initialize Database
db.init_db()

# --- Page Config ---
st.set_page_config(page_title="Intellektual Bellashuv", page_icon="🎓", layout="wide")

# --- Custom CSS (Modern UI/UX) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphism Effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 20px; /* Reduced top/bottom padding */
        margin-bottom: 20px;
    }

    /* Stat Cards */
    .stat-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .stat-card {
        flex: 1;
        min-width: 200px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(168, 85, 247, 0.2);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(168, 85, 247, 0.5);
    }
    .stat-val {
        font-size: 2rem;
        font-weight: 800;
        color: #f8fafc;
        display: block;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Modern Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.2rem;
        font-weight: 600;
        background: linear-gradient(135deg, #4f46e5, #9333ea);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(147, 51, 234, 0.6), 0 0 10px rgba(79, 70, 229, 0.4);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .stButton > button:active {
        transform: scale(0.98);
        box-shadow: 0 0 40px rgba(147, 51, 234, 0.8);
    }

    /* Question Cards */
    .q-card {
        background: rgba(30, 41, 59, 0.5);
        border-left: 5px solid #6366f1;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }

    /* Headers */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem; /* Reduced from 3rem */
        margin-top: -2rem;
    }

    /* Badge Style */
    .badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-pending { background: rgba(234, 179, 8, 0.2); color: #eab308; }
    .badge-started { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .badge-finished { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

    /* Custom Contact Footer */
    .contact-footer {
        text-align: center;
        margin-top: 5rem;
        padding: 30px;
        border-top: 1px solid rgba(255,255,255,0.05);
        color: #64748b;
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
    if not start_time: return limit
    elapsed = time.time() - start_time
    remaining = limit - elapsed
    return max(0, remaining)

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

# --- Pages ---

def super_admin_page():
    st.markdown("<h1 style='text-align: center;'>🔑 Super Admin Paneli</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("⬅️ Chiqish", key="super_exit"):
            clear_session()
            st.rerun()

    tab1, tab2 = st.tabs(["🎮 Barcha Musobaqalar", "➕ Yangi Yaratish"])
    
    with tab1:
        comps = db.get_all_competitions()
        if not comps:
            st.info("Hozircha musobaqalar yo'q.")
        else:
            for c in comps:
                badge_class = f"badge-{c['status']}"
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin:0;">📍 {c['name']}</h3>
                        <span class="badge {badge_class}">{c['status'].upper()}</span>
                    </div>
                    <p style="color: #94a3b8; margin-top: 10px;">Kod: <b>{c['code']}</b> | Parol: <b>{c['admin_password']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns([1, 4])
                if c1.button("Kirish", key=f"go_{c['id']}"):
                    st.session_state["role"] = "admin"
                    st.session_state["comp_id"] = c['id']
                    save_session("admin", comp_id=c['id'])
                    st.rerun()
                if c1.button("O'chirish", key=f"del_{c['id']}"):
                    db.delete_competition(c['id'])
                    st.rerun()

    with tab2:
        with st.form("new_comp_form"):
            name = st.text_input("Musobaqa nomi")
            code = st.text_input("4 xonali kod", max_chars=9)
            admin_pass = st.text_input("Admin paroli")
            time_limit = st.number_input("Vaqt (daqiqa)", min_value=1, value=30)
            if st.form_submit_button("Yaratish"):
                if name and code and admin_pass:
                    res = db.create_competition(name, code, admin_pass, time_limit)
                    if res: st.success("Yaratildi!"); st.rerun()
                    else: st.error("Xato!")

def login_page():
    st.markdown("<h1 class='main-header'>Intellektual Bellashuv</h1>", unsafe_allow_html=True)
    
    if "temp_comp" not in st.session_state:
        st.session_state["temp_comp"] = None

    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        if not st.session_state["temp_comp"]:
            st.markdown("""
                <div class="glass-card">
                    <h3 style="margin-top:0; margin-bottom:15px; text-align:center;">Musobaqa kodini kiriting</h3>
            """, unsafe_allow_html=True)
            comp_code = st.text_input("Imtihon kodi", key="main_code_input", placeholder="Masalan: 1234", label_visibility="collapsed")
            if st.button("Davom etish"):
                if comp_code == "502500560":
                    st.session_state["role"] = "super_admin"
                    save_session("super_admin")
                    st.rerun()
                comp = db.get_competition_by_code(comp_code)
                if comp:
                    st.session_state["temp_comp"] = comp
                    st.rerun()
                else: st.error("Noto'g'ri kod!")
        else:
            comp = st.session_state["temp_comp"]
            st.markdown(f"<h3 style='text-align: center; color: #38bdf8;'>{comp['name']}</h3>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🎓 O'quvchi", "🛡️ Admin"])
            with tab1:
                f_name = st.text_input("Ism")
                l_name = st.text_input("Familiya")
                pwd = st.text_input("Parol", type="password")
                if st.button("O'quvchi bo'lib kirish"):
                    if f_name and l_name and pwd:
                        student = db.get_student_by_login(comp['id'], f_name, l_name, pwd)
                        if not student:
                            try:
                                student_id = db.add_student(comp['id'], f_name, l_name, pwd)
                                student = db.get_student(student_id)
                            except: st.error("Xato!")
                        
                        if student:
                            st.session_state["role"] = "student"
                            st.session_state["student_id"] = student['id']
                            st.session_state["comp_id"] = comp['id']
                            save_session("student", comp_id=comp['id'], student_id=student['id'])
                            st.rerun()
            with tab2:
                admin_pwd = st.text_input("Admin paroli", type="password")
                if st.button("Admin bo'lib kirish"):
                    if admin_pwd == comp['admin_password']:
                        st.session_state["role"] = "admin"
                        st.session_state["comp_id"] = comp['id']
                        save_session("admin", comp_id=comp['id'])
                        st.rerun()
                    else: st.error("Xato!")
            
            if st.button("⬅️ Orqaga"):
                st.session_state["temp_comp"] = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="contact-footer">
            <p>Savollar bo'yicha bog'lanish: <br>
            <a href="tel:+998502500560" style="color: #38bdf8; text-decoration: none; font-weight: bold;">📞 +998 50 250 05 60</a></p>
        </div>
    """, unsafe_allow_html=True)

def admin_page():
    comp_id = st.session_state.get("comp_id")
    comp = db.get_competition_by_id(comp_id)
    if not comp: clear_session(); st.rerun()

    st_autorefresh(interval=5000, key="admin_refresh")
    
    # Header with Stats
    st.markdown(f"<h1>🛡️ Admin: {comp['name']}</h1>", unsafe_allow_html=True)
    
    students = db.get_all_students(comp_id)
    questions_db = db.get_all_questions(comp_id)
    max_score = max([s['score'] for s in students]) if students else 0
    
    st.markdown(f"""
    <div class="stat-container">
        <div class="stat-card">
            <span class="stat-label">O'quvchilar</span>
            <span class="stat-val">{len(students)}</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Biletlar</span>
            <span class="stat-val">20</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Eng yuqori ball</span>
            <span class="stat-val">{max_score}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Reyting & Boshqaruv", "🎫 Biletlar", "📝 Savollar"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            head_col1, head_col2 = st.columns([3, 1])
            with head_col1:
                st.markdown("<h3>Jonli Reyting</h3>", unsafe_allow_html=True)
            with head_col2:
                if st.button("🧹 Filter", key="filter_btn"):
                    db.delete_inactive_students(comp_id)
                    st.success("O'chirildi!")
                    time.sleep(1)
                    st.rerun()
            
            if students:
                df = pd.DataFrame(students)
                df["Bilet"] = df["ticket_number"].apply(lambda x: f"№{x}" if x else "-")
                df["Togri"] = df["solved_questions"].apply(len)
                df["Xato"] = df["failed_questions"].apply(len)
                df["Natija"] = df["Togri"].apply(lambda x: f"{x} (20 taladan)")
                
                ranks = [f"👑 {i+1}" if i < 3 else str(i+1) for i in range(len(df))]
                df["O'rin"] = ranks
                
                final_df = df[["O'rin", 'first_name', 'last_name', 'Bilet', "Togri", "Xato", "Natija"]]
                final_df.columns = ["O'rin", "Ism", "Familiya", "Bilet", "To'g'ri", "Xato", "Natija"]
                st.dataframe(final_df, use_container_width=True, hide_index=True)
            else: st.info("Hali hech kim yo'q.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        with col2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Boshqaruv")
            status = comp['status']
            badge_class = f"badge-{status}"
            st.markdown(f"Holat: <span class='badge {badge_class}'>{status.upper()}</span>", unsafe_allow_html=True)
            
            # Time limit
            current_min = comp['time_limit'] // 60
            new_limit = st.number_input("⏳ Vaqt (daqiqa)", min_value=1, value=current_min, disabled=(status == 'started'))
            if new_limit != current_min:
                db.update_competition_time_limit(comp_id, new_limit * 60)
                st.rerun()

            if status == 'pending':
                if st.button("🟢 Boshlash"):
                    db.update_competition_status(comp_id, 'started', start_time=time.time())
                    st.rerun()
                if st.button("🎟️ Biletlarni tarqatish"):
                    db.assign_tickets_randomly(comp_id)
                    st.success("Biletlar muvaffaqiyatli tarqatildi!")
                    time.sleep(1)
                    st.rerun()
            elif status == 'started':
                time_left = get_time_left(comp)
                if time_left > 0:
                    import streamlit.components.v1 as components
                    end_ts = time.time() + time_left
                    html_timer = f"""<div style="font-family:sans-serif;background:#1e293b;color:#38bdf8;padding:10px;border-radius:10px;text-align:center;font-size:1.5rem;font-weight:800;border:2px solid #38bdf8;margin-bottom:5px;">⏳ <span id="at">--:--</span></div>
                    <script>var et={end_ts}*1000;function ut(){{var n=new Date().getTime();var d=et-n;if(d<=0){{document.getElementById('at').innerHTML="00:00";return;}}var m=Math.floor((d%(1000*60*60))/(1000*60)).toString().padStart(2,'0');var s=Math.floor((d%(1000*60))/1000).toString().padStart(2,'0');document.getElementById('at').innerHTML=m+":"+s;}}setInterval(ut,1000);ut();</script>"""
                    components.html(html_timer, height=80)
                    if st.button("🛑 To'xtatish"):
                        db.update_competition_status(comp_id, 'finished'); st.rerun()
                else: db.update_competition_status(comp_id, 'finished'); st.rerun()
            else:
                if st.button("🔄 Nollash"): db.reset_scores(comp_id); st.rerun()

            if st.button("🚪 Chiqish"): clear_session(); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<h3>Barcha Biletlar</h3>", unsafe_allow_html=True)
        for t_num in range(1, 21):
            with st.expander(f"🎫 Bilet №{t_num}"):
                t_qs = db.get_ticket_questions(comp_id, t_num)
                if t_qs:
                    for i, q in enumerate(t_qs):
                        st.write(f"**{i+1}.** {q['question']} *(Turi: {q['type']})*")
                else:
                    st.info("Bu bilet hali generatsiya qilinmagan. 'Boshqaruv' bo'limidan biletlarni tarqating.")

    with tab3:
        for idx, q in enumerate(questions_db):
            st.markdown(f"""
            <div class="q-card">
                <b>{idx+1}. {q['topic']}</b><br>
                {q['question']}
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{q['id']}"):
                db.delete_question(q['id']); st.rerun()
        
        with st.expander("➕ Yangi savol"):
            with st.form("add_q"):
                t = st.text_input("Mavzu"); q_txt = st.text_area("Savol"); a = st.text_input("Javob"); s = st.number_input("Ball", value=10)
                if st.form_submit_button("Saqlash"):
                    if t and q_txt and a: db.add_question(comp_id, t, q_txt, a, s); st.rerun()

def student_page():
    student_id = st.session_state.get("student_id")
    comp_id = st.session_state.get("comp_id")
    student = db.get_student(student_id)
    comp = db.get_competition_by_id(comp_id)
    
    if not student or not comp: clear_session(); st.rerun()
        
    solved = student.get("solved_questions", [])
    questions_db = db.get_all_questions(comp_id)
    
    st.sidebar.markdown(f"""
    <div class="glass-card" style="padding:15px; text-align:center;">
        <h2 style="margin:0;">👤</h2>
        <h4 style="margin:5px 0;">{student['first_name']} {student['last_name']}</h4>
        <div style="font-size:1.5rem; font-weight:800; color:#22c55e;">{len(solved)} <small style="font-size:0.7rem; color:#94a3b8;">TO'G'RI</small></div>
        <div style="font-size:1rem; font-weight:600; color:#ef4444;">{len(student.get('failed_questions', []))} <small style="font-size:0.7rem; color:#94a3b8;">XATO</small></div>
    </div>
    """, unsafe_allow_html=True)

    # --- Formula Panel ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("📚 Ehtimollik va Statistika Formulalari", expanded=False):
            st.markdown("#### 1. Kombinatorika")
            st.latex(r"P_n = n! \quad \text{(O'rin almashtirish)}")
            st.latex(r"A_n^k = \frac{n!}{(n-k)!} \quad \text{(O'rinlashtirish)}")
            st.latex(r"C_n^k = \frac{n!}{k!(n-k)!} \quad \text{(Guruhlash)}")
            
            st.markdown("#### 2. Ehtimollik Ta'rifi")
            st.latex(r"P(A) = \frac{m}{n} \quad (0 \le P(A) \le 1)")
            st.latex(r"P(\bar{A}) = 1 - P(A) \quad \text{(Zidd hodisa)}")
            
            st.markdown("#### 3. Qo'shish va Ko'paytirish")
            st.latex(r"P(A+B) = P(A) + P(B) - P(AB)")
            st.latex(r"P(AB) = P(A) \cdot P(B|A)")
            
            st.markdown("#### 4. To'la ehtimollik va Bayes")
            st.latex(r"P(A) = \sum_{i=1}^n P(H_i)P(A|H_i)")
            st.latex(r"P(H_i|A) = \frac{P(H_i)P(A|H_i)}{P(A)}")
            
            st.markdown("#### 5. Bernulli Sxemasi")
            st.latex(r"P_n(k) = C_n^k p^k q^{n-k}")
            st.latex(r"P_n(k) \approx \frac{\lambda^k e^{-\lambda}}{k!} \quad (\text{Puasson})")
            
            st.markdown("#### 6. Tasodifiy Miqdorlar")
            st.latex(r"M(X) = \sum x_i p_i \quad \text{(Mat. kutilma)}")
            st.latex(r"D(X) = M(X^2) - [M(X)]^2 \quad \text{(Dispersiya)}")
            st.latex(r"\sigma(X) = \sqrt{D(X)} \quad \text{(O'rtacha kvadratik chetlanish)}")

        with st.expander("🧮 Formula Kalkulyatori", expanded=True):
            f_type = st.selectbox("Hisoblash uchun formulani tanlang:", [
                "Tanlang...", "P(n) - O'rin almashtirish", "A(n, k) - O'rinlashtirish", 
                "C(n, k) - Guruhlash", "P(A) = m/n", "Bernulli formulasi"
            ])
            
            if f_type == "P(n) - O'rin almashtirish":
                n_val = st.number_input("n =", min_value=0, max_value=170, step=1, key="calc_n_p")
                st.success(f"Natija: {math.factorial(n_val):,}")
            
            elif f_type == "A(n, k) - O'rinlashtirish":
                n_val = st.number_input("n =", min_value=0, step=1, key="calc_n_a")
                k_val = st.number_input("k =", min_value=0, max_value=n_val, step=1, key="calc_k_a")
                res = math.perm(n_val, k_val)
                st.success(f"Natija: {res:,}")
                
            elif f_type == "C(n, k) - Guruhlash":
                n_val = st.number_input("n =", min_value=0, step=1, key="calc_n_c")
                k_val = st.number_input("k =", min_value=0, max_value=n_val, step=1, key="calc_k_c")
                res = math.comb(n_val, k_val)
                st.success(f"Natija: {res:,}")
                
            elif f_type == "P(A) = m/n":
                m_val = st.number_input("m (qulay hollar) =", min_value=0, step=1, key="calc_m")
                n_val = st.number_input("n (barcha hollar) =", min_value=1, step=1, key="calc_n_prob")
                st.success(f"Natija: {round(m_val/n_val, 4)}")
                
            elif f_type == "Bernulli formulasi":
                col1, col2 = st.columns(2)
                n_val = col1.number_input("n (jami) =", min_value=1, step=1, key="calc_n_b")
                k_val = col2.number_input("k (kerakli) =", min_value=0, max_value=n_val, step=1, key="calc_k_b")
                p_val = st.number_input("p (ehtimollik) =", min_value=0.0, max_value=1.0, value=0.5, step=0.01, key="calc_p_b")
                q_val = 1 - p_val
                res = math.comb(n_val, k_val) * (p_val**k_val) * (q_val**(n_val-k_val))
                st.success(f"Natija: {round(res, 6)}")
    
    if comp['status'] == 'started':
        time_left = get_time_left(comp)
        if time_left > 0:
            st_autorefresh(interval=5000, key="st_active")
            db.update_last_active(student_id)
            
            # Timer display
            import streamlit.components.v1 as components
            end_ts = time.time() + time_left
            html_st_timer = f"""<div style="font-family:sans-serif;background:#0f172a;color:#f43f5e;padding:10px;border-radius:10px;text-align:center;font-size:1.2rem;font-weight:800;border:2px solid #f43f5e;margin-bottom:5px;"><span id="st">--:--</span></div>
            <script>var et={end_ts}*1000;function ut(){{var n=new Date().getTime();var d=et-n;if(d<=0){{document.getElementById('st').innerHTML="TUGADI";return;}}var m=Math.floor((d%(1000*60*60))/(1000*60)).toString().padStart(2,'0');var s=Math.floor((d%(1000*60))/1000).toString().padStart(2,'0');document.getElementById('st').innerHTML="⏳ "+m+":"+s;}}setInterval(ut,1000);ut();</script>"""
            st.sidebar.markdown("---")
            with st.sidebar: components.html(html_st_timer, height=80)
            
            ticket_num = student.get('ticket_number')
            if not ticket_num:
                st.warning("⚠️ Sizga hali bilet biriktirilmagan. Admin biletlarni tarqatishini kuting.")
                return

            st.markdown(f"## 🎫 Bilet №{ticket_num}")
            
            solved = student.get("solved_questions", [])
            failed = student.get("failed_questions", [])
            
            questions_db = db.get_ticket_questions(comp_id, ticket_num)
            
            for idx, q in enumerate(questions_db):
                q_id = q['id']
                is_solved = q_id in solved
                is_failed = q_id in failed
                
                if is_solved: icon, color = "✅", "#22c55e"
                elif is_failed: icon, color = "❌", "#ef4444"
                else: icon, color = "⏳", "#94a3b8"
                
                st.markdown(f"#### {icon} {idx+1}-savol")
                st.markdown(f"<div class='q-card' style='border-left-color: {color};'>{q['question']}</div>", unsafe_allow_html=True)
                
                if is_solved:
                    st.success("To'g'ri javob berilgan!")
                elif is_failed:
                    st.error("Xato javob berilgan! Imkoniyat tugadi.")
                else:
                    with st.form(key=f"f_{q_id}"):
                        if q['type'] == 'test':
                            options = json.loads(q['options']) if q['options'] else []
                            ans = st.radio("Variantlardan birini tanlang:", options, key=f"radio_{q_id}")
                        else:
                            ans = st.text_input("Javobingizni yozing:", key=f"input_{q_id}")
                            
                        if st.form_submit_button("Yuborish"):
                            user_ans = str(ans).strip().replace(" ","").replace(",",".").lower()
                            correct_options = [a.strip().replace(" ","").replace(",",".").lower() for a in str(q["answer"]).split("|")]
                            
                            if user_ans in correct_options:
                                st.balloons()
                                db.update_student_progress(student_id, solved + [q_id], failed)
                                st.rerun()
                            else:
                                db.update_student_progress(student_id, solved, failed + [q_id])
                                st.error("Noto'g'ri javob!")
                                time.sleep(1)
                                st.rerun()
                st.markdown("---")
        else:
            st.error("Vaqt tugadi!")
    elif comp['status'] == 'finished':
        st.markdown("<div class='glass-card' style='text-align:center;'><h1>🏁 Musobaqa Yakunlandi</h1>", unsafe_allow_html=True)
        st.write(f"Sizning ballingiz: **{student['score']}**")
        st.markdown("</div>", unsafe_allow_html=True)
        # Leaderboard
        students = db.get_all_students(comp_id)
        df = pd.DataFrame(students)
        df['Natija'] = df['solved_questions'].apply(lambda x: f"{len(x)} (20 taladan)")
        df = df[["first_name", "last_name", "score", "Natija"]].rename(columns={"first_name":"Ism","last_name":"Familiya","score":"Ball"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st_autorefresh(interval=5000, key="st_wait")
        st.markdown("<div style='text-align:center; margin-top:20vh;'><h1>⏳ Tayyor turing!</h1><p>Musobaqa yaqin daqiqalarda boshlanadi.</p></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Chiqish"): clear_session(); st.rerun()

# --- Main Logic ---
role = st.session_state.get("role")
if role == "super_admin": super_admin_page()
elif role == "admin": admin_page()
elif role == "student": student_page()
else: login_page()
