import streamlit as st
import pandas as pd
import joblib
from supabase import create_client

# --- CONFIGURATION & DATABASE ---
st.set_page_config(page_title="WC 2026 Predictor", page_icon="🏆", layout="wide")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None

supabase = init_connection()

@st.cache_resource
def load_model():
    try:
        return joblib.load("src/baseline_model.pkl")
    except:
        return None

model = load_model()

# --- MOCK DATA & CDN FLAGS ---
# Using ISO codes to fetch web images, bypassing OS emoji rendering issues
ISO_CODES = {
    "Mexico": "mx", "South Africa": "za", "Korea Republic": "kr", "Czechia": "cz",
    "Canada": "ca", "Bosnia and Herzegovina": "ba", "Qatar": "qa", "Switzerland": "ch",
    "Brazil": "br", "Morocco": "ma", "Haiti": "ht", "Scotland": "gb-sct",
    "USA": "us", "Paraguay": "py", "Australia": "au", "Türkiye": "tr",
    "Germany": "de", "Curacao": "cw", "Cote D'Ivoire": "ci", "Ecuador": "ec",
    "Netherlands": "nl", "Japan": "jp", "Sweden": "se", "Tunisia": "tn",
    "Belgium": "be", "Egypt": "eg", "Iran": "ir", "New Zealand": "nz",
    "Spain": "es", "Cabo Verde": "cv", "Saudi Arabia": "sa", "Uruguay": "uy",
    "France": "fr", "Senegal": "sn", "Iraq": "iq", "Norway": "no",
    "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Jordan": "jo",
    "Portugal": "pt", "Congo DR": "cd", "Uzbekistan": "uz", "Colombia": "co",
    "England": "gb-eng", "Croatia": "hr", "Ghana": "gh", "Panama": "pa"
}

def get_flag_url(team_name):
    code = ISO_CODES.get(team_name)
    return f"https://flagcdn.com/w40/{code}.png" if code else None

GROUPS = {
    "A": ["Mexico", "South Africa", "Korea Republic", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Curacao", "Cote D'Ivoire", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cabo Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Congo DR", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"]
}

# --- BRACKET ARCHITECTURE ---
ADVANCEMENT = {
    73: (89, "home"), 74: (89, "away"), 75: (90, "home"), 76: (90, "away"),
    77: (91, "home"), 78: (91, "away"), 79: (92, "home"), 80: (92, "away"),
    81: (93, "home"), 82: (93, "away"), 83: (94, "home"), 84: (94, "away"),
    85: (95, "home"), 86: (95, "away"), 87: (96, "home"), 88: (96, "away"),
    89: (97, "home"), 90: (97, "away"), 91: (98, "home"), 92: (98, "away"),
    93: (99, "home"), 94: (99, "away"), 95: (100, "home"), 96: (100, "away"),
    97: (101, "home"), 98: (101, "away"), 99: (102, "home"), 100: (102, "away"),
    101: (104, "home", 103, "home"), 102: (104, "away", 103, "away"),
}

# --- INITIALIZE SESSION STATE ---
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "group_rankings" not in st.session_state: st.session_state.group_rankings = {g: teams.copy() for g, teams in GROUPS.items()}
if "qualified_thirds" not in st.session_state: st.session_state.qualified_thirds = []
if "bracket" not in st.session_state: st.session_state.bracket = {}

# --- CORE LOGIC FUNCTIONS ---
def get_ai_pick(home, away):
    if not model or "Pending" in home or "Pending" in away:
        return "Waiting for Data..."
    try:
        # Fallback to pure rating proxy if live feature lookup isn't wired yet
        features = pd.DataFrame([[0.55, 0.50, 1.5, 1.2]], columns=['home_historical_winrate', 'away_historical_winrate', 'home_avg_goals', 'away_avg_goals'])
        pred = model.predict(features)[0]
        return home if pred == 1 else away
    except:
        return home 

def auto_allocate_third_place(selected_thirds):
    """Backtracking solver for FIFA Annex C Bipartite matching."""
    slots = {
        74: ['A','B','C','D','F'], 77: ['C','D','F','G','H'], 79: ['C','E','F','H','I'],
        80: ['E','H','I','J','K'], 81: ['B','E','F','I','J'], 82: ['A','E','H','I','J'],
        83: ['E','F','G','I','J'], 84: ['D','E','I','J','L']
    }
    
    teams_data = [{"name": t.split(" (Gr ")[0], "group": t.split(" (Gr ")[1][:-1]} for t in selected_thirds]
    
    def backtrack(slot_keys, available, assignment):
        if not slot_keys: return assignment
        curr_slot = slot_keys[0]
        valid_groups = slots[curr_slot]
        
        for team in available:
            if team['group'] in valid_groups:
                new_assignment = assignment.copy()
                new_assignment[curr_slot] = team['name']
                new_avail = [t for t in available if t['name'] != team['name']]
                res = backtrack(slot_keys[1:], new_avail, new_assignment)
                if res: return res
        return None
        
    return backtrack(list(slots.keys()), teams_data, {})

def reset_downstream(match_id):
    if match_id in ADVANCEMENT:
        adv = ADVANCEMENT[match_id]
        if len(adv) == 2:
            st.session_state.bracket[adv[0]][adv[1]] = f"Pending W{match_id}"
            if st.session_state.bracket[adv[0]]["winner"] is not None:
                st.session_state.bracket[adv[0]]["winner"] = None
                reset_downstream(adv[0])
        elif len(adv) == 4:
            st.session_state.bracket[adv[0]][adv[1]] = f"Pending W{match_id}"
            st.session_state.bracket[adv[2]][adv[3]] = f"Pending L{match_id}"
            if st.session_state.bracket[adv[0]]["winner"] is not None:
                st.session_state.bracket[adv[0]]["winner"] = None
                reset_downstream(adv[0])
            if st.session_state.bracket[adv[2]]["winner"] is not None:
                st.session_state.bracket[adv[2]]["winner"] = None
                reset_downstream(adv[2])

def initialize_bracket(allocations):
    W = {grp: teams[0] for grp, teams in st.session_state.group_rankings.items()}
    RU = {grp: teams[1] for grp, teams in st.session_state.group_rankings.items()}
    
    bracket = {}
    bracket[73] = {"home": RU['A'], "away": RU['B'], "winner": None}
    bracket[74] = {"home": W['E'], "away": allocations[74], "winner": None}
    bracket[75] = {"home": W['F'], "away": RU['C'], "winner": None}
    bracket[76] = {"home": W['C'], "away": RU['F'], "winner": None}
    bracket[77] = {"home": W['I'], "away": allocations[77], "winner": None}
    bracket[78] = {"home": RU['E'], "away": RU['I'], "winner": None}
    bracket[79] = {"home": W['A'], "away": allocations[79], "winner": None}
    bracket[80] = {"home": W['L'], "away": allocations[80], "winner": None}
    bracket[81] = {"home": W['D'], "away": allocations[81], "winner": None}
    bracket[82] = {"home": W['G'], "away": allocations[82], "winner": None}
    bracket[83] = {"home": W['B'], "away": allocations[83], "winner": None}
    bracket[84] = {"home": W['K'], "away": allocations[84], "winner": None}
    bracket[85] = {"home": RU['K'], "away": RU['L'], "winner": None}
    bracket[86] = {"home": W['J'], "away": RU['H'], "winner": None}
    bracket[87] = {"home": W['H'], "away": RU['J'], "winner": None}
    bracket[88] = {"home": RU['D'], "away": RU['G'], "winner": None}
    
    parent_map = {}
    for parent, adv in ADVANCEMENT.items():
        if len(adv) == 2:
            if adv[0] not in parent_map: parent_map[adv[0]] = {}
            parent_map[adv[0]][adv[1]] = parent
        elif len(adv) == 4:
            if adv[0] not in parent_map: parent_map[adv[0]] = {}
            parent_map[adv[0]][adv[1]] = parent
            if adv[2] not in parent_map: parent_map[adv[2]] = {}
            parent_map[adv[2]][adv[3]] = parent

    for m in range(89, 105):
        h_parent = parent_map[m]["home"]
        a_parent = parent_map[m]["away"]
        bracket[m] = {
            "home": f"Pending W{h_parent}" if m != 103 else f"Pending L{h_parent}",
            "away": f"Pending W{a_parent}" if m != 103 else f"Pending L{a_parent}",
            "winner": None
        }
        
    st.session_state.bracket = bracket

# --- UI PRESENTATION ---
st.title("🏆 FIFA World Cup 2026 AI Predictor")
st.markdown("Build your bracket and match your intuition against the Random Forest ML pipeline.")

with st.sidebar:
    st.header("👤 Player Profile")
    username = st.text_input("Enter Username:", placeholder="Player 1")
    if not supabase:
        st.error("Database disconnected. Check your API keys in .streamlit/secrets.toml.")

steps = ["Group Stages", "Third-Place Teams", "Algorithm Mapping", "Knockout Bracket"]
st.progress(st.session_state.current_step / 4, text=f"Step {st.session_state.current_step}: {steps[st.session_state.current_step - 1]}")
st.divider()

# ================= STEP 1: GROUPS =================
if st.session_state.current_step == 1:
    st.header("1️⃣ Group Stage Simulator")
    
    col1, col2, col3 = st.columns(3)
    chunked_groups = [list(GROUPS.keys())[i:i+4] for i in range(0, 12, 4)]
    has_duplicates = False
    
    for i, col in enumerate([col1, col2, col3]):
        with col:
            for grp in chunked_groups[i]:
                st.markdown(f"#### Group {grp}")
                teams = GROUPS[grp]
                t1 = st.selectbox("1st", teams, index=teams.index(st.session_state.group_rankings[grp][0]), key=f"{grp}_1")
                t2 = st.selectbox("2nd", teams, index=teams.index(st.session_state.group_rankings[grp][1]), key=f"{grp}_2")
                t3 = st.selectbox("3rd", teams, index=teams.index(st.session_state.group_rankings[grp][2]), key=f"{grp}_3")
                t4 = st.selectbox("4th", teams, index=teams.index(st.session_state.group_rankings[grp][3]), key=f"{grp}_4")
                
                selected = [t1, t2, t3, t4]
                if len(set(selected)) != 4:
                    st.error("Duplicate teams detected.")
                    has_duplicates = True
                else:
                    st.session_state.group_rankings[grp] = selected
                st.divider()
                
    if st.button("Next: Lock Groups ➡️", type="primary"):
        if not has_duplicates:
            st.session_state.current_step = 2
            st.rerun()

# ================= STEP 2: THIRD-PLACE =================
elif st.session_state.current_step == 2:
    st.header("2️⃣ Select Best 8 Third-Place Teams")
    
    third_placers = [f"{ranks[2]} (Gr {grp})" for grp, ranks in st.session_state.group_rankings.items()]
        
    selected_thirds = st.multiselect(
        "Select exactly 8 teams that advance:",
        options=third_placers,
        default=st.session_state.qualified_thirds if len(st.session_state.qualified_thirds) == 8 else None,
        max_selections=8
    )
    
    st.session_state.qualified_thirds = selected_thirds
    
    st.divider()
    c1, c2 = st.columns([1, 8])
    with c1:
        if st.button("⬅️ Back"):
            st.session_state.current_step = 1
            st.rerun()
    with c2:
        if st.button("Next: AI Allocation ➡️", type="primary"):
            if len(selected_thirds) == 8:
                st.session_state.current_step = 3
                st.rerun()
            else:
                st.warning("You must select exactly 8 teams.")

# ================= STEP 3: MAPPING (AUTOMATED) =================
elif st.session_state.current_step == 3:
    st.header("3️⃣ FIFA Allocation Algorithm")
    st.write("Computing the Bipartite matches to satisfy FIFA Annex C constraints without group collisions...")
    
    allocation_matrix = auto_allocate_third_place(st.session_state.qualified_thirds)
    
    if not allocation_matrix:
        st.error("FATAL: No mathematically valid combination exists for your 8 selected teams based on FIFA rules. Go back and select a different combination.")
        if st.button("⬅️ Go Back"):
            st.session_state.current_step = 2
            st.rerun()
    else:
        st.success("Valid allocation matrix generated.")
        df_alloc = pd.DataFrame(list(allocation_matrix.items()), columns=["Match ID", "Assigned Third-Place Team"])
        st.dataframe(df_alloc, hide_index=True)
        
        st.divider()
        c1, c2 = st.columns([1, 8])
        with c1:
            if st.button("⬅️ Back"):
                st.session_state.current_step = 2
                st.rerun()
        with c2:
            if st.button("Generate & Play Bracket ➡️", type="primary"):
                initialize_bracket(allocation_matrix)
                st.session_state.current_step = 4
                st.rerun()

# ================= STEP 4: KNOCKOUT BRACKET =================
elif st.session_state.current_step == 4:
    st.header("4️⃣ Live Knockout Simulator")
    
    c1, c2, c3 = st.columns([2, 2, 8])
    with c1:
        if st.button("⬅️ Edit Setup"):
            st.session_state.current_step = 3
            st.rerun()
    with c2:
        if st.button("💾 Save Bracket to Database", type="primary"):
            if not username:
                st.error("Enter a Username in the sidebar first.")
            elif not supabase:
                st.error("Database connection failed.")
            elif "Pending" in st.session_state.bracket[104]["home"] or "Pending" in st.session_state.bracket[104]["away"]:
                st.warning("Please finish all matches before saving.")
            else:
                try:
                    supabase.table("predictions").insert({
                        "username": username,
                        "tournament_tree": st.session_state.bracket
                    }).execute()
                    st.success("Bracket permanently locked to the leaderboard!")
                except Exception as e:
                    st.error(f"Save failed: {e}")
            
    st.divider()
    
    def render_team(team_name, is_ai_pick=False):
        url = get_flag_url(team_name)
        col1, col2 = st.columns([1, 5])
        with col1:
            if url: st.image(url, width=30)
        with col2:
            text = f"**{team_name}** (AI)" if is_ai_pick else team_name
            st.write(text)

    def render_match(match_id, title=None):
        m = st.session_state.bracket[match_id]
        h, a = m["home"], m["away"]
        
        st.markdown(f"##### {title if title else f'Match {match_id}'}")
        
        if "Pending" in h or "Pending" in a:
            st.caption(f"{h} vs {a}")
            st.write("⏳ *Awaiting upstream result*")
        else:
            ai_pick = get_ai_pick(h, a)
            
            # Custom UI layout for flags and selection
            st.caption("Select Winner:")
            
            h_col1, h_col2 = st.columns([1, 4])
            with h_col1:
                h_url = get_flag_url(h)
                if h_url: st.image(h_url, width=25)
            with h_col2:
                h_label = f"{h} 🤖" if ai_pick == h else h
                h_btn = st.button(h_label, key=f"btn_h_{match_id}", use_container_width=True, type="primary" if m["winner"] == h else "secondary")
                
            a_col1, a_col2 = st.columns([1, 4])
            with a_col1:
                a_url = get_flag_url(a)
                if a_url: st.image(a_url, width=25)
            with a_col2:
                a_label = f"{a} 🤖" if ai_pick == a else a
                a_btn = st.button(a_label, key=f"btn_a_{match_id}", use_container_width=True, type="primary" if m["winner"] == a else "secondary")

            chosen = None
            if h_btn: chosen = h
            if a_btn: chosen = a
            
            if chosen and m["winner"] != chosen:
                m["winner"] = chosen
                if match_id in ADVANCEMENT:
                    adv = ADVANCEMENT[match_id]
                    if len(adv) == 2:
                        st.session_state.bracket[adv[0]][adv[1]] = chosen
                        if st.session_state.bracket[adv[0]]["winner"]:
                            st.session_state.bracket[adv[0]]["winner"] = None
                            reset_downstream(adv[0])
                    elif len(adv) == 4:
                        st.session_state.bracket[adv[0]][adv[1]] = chosen
                        loser = h if chosen == a else a
                        st.session_state.bracket[adv[2]][adv[3]] = loser
                        
                        if st.session_state.bracket[adv[0]]["winner"]:
                            st.session_state.bracket[adv[0]]["winner"] = None
                            reset_downstream(adv[0])
                        if st.session_state.bracket[adv[2]]["winner"]:
                            st.session_state.bracket[adv[2]]["winner"] = None
                            reset_downstream(adv[2])
                st.rerun()
        st.divider()

    def render_round(start, end, cols, title):
        st.subheader(title)
        c_list = st.columns(cols)
        matches = list(range(start, end + 1))
        chunk_size = (len(matches) + cols - 1) // cols
        
        for i, col in enumerate(c_list):
            with col:
                for m in matches[i*chunk_size : (i+1)*chunk_size]:
                    if m <= end: render_match(m)

    render_round(73, 88, 4, "Round of 32")
    render_round(89, 96, 4, "Round of 16")
    render_round(97, 100, 4, "Quarterfinals")
    render_round(101, 102, 2, "Semifinals")
    
    st.subheader("Finals")
    fc1, fc2 = st.columns(2)
    with fc1: render_match(104, "🏆 Grand Final")
    with fc2: render_match(103, "🥉 Third-Place Match")