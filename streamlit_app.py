# Import the external library
# Import the function from season_data.py
from scripts.current_standings import fetch_current_standings
import streamlit as st
import streamlit.components.v1 as components
from streamlit_echarts import st_echarts
import traceback 
import altair as alt
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend

import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)

st.set_page_config(page_title="Check This Data", 
                   page_icon="🏒", 
                   initial_sidebar_state="expanded",
                   layout="wide",)

# image = Image.open('logo.png')
# st.image(image)

primaryColor="#fafaff"
backgroundColor="#e1dee9"
secondaryBackgroundColor="#d5cfe1"
textColor="#262730"
font="Garamond"




option = {
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Eastern", "Western"]},
    "xAxis": {
        "type": "category",
        "data": ["2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
                    "2021-22", "2022-23", "2023-24", "2024-25"]
    },
    "yAxis": {"type": "value"},
    "series": [
        {
            "name": "Eastern",
            "type": "line",
            "smooth": True,
            "data": [0.750, 0.625, 0.750, 0.750, 0.625, 0.875, 0.875, 0.875, 0.750]
        },
        {
            "name": "Western",
            "type": "line",
            "smooth": True,
            "data": [0.875, 0.875, 0.875, 0.625, 0.750, 0.625, 0.750, 0.750, 0.750]
        }
    ]
}


  
##########################################
##  Tab Styling                         ##
##########################################


st.markdown("""
<style>

    /* Inactive tab styling */
    button[data-baseweb="tab"] {
        border-bottom: 3px solid transparent !important;
        color: #cccccc !important; /* Silver Line */
        font-size: 75px !important;       /* <<< increase tab font size */
        padding: 10px 20px !important;     /* <<< optional: more spacing */
    }

    /* ACTIVE tab */
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 2px solid #2c7da0 !important; /* Blue active tab underline */
        color: white !important;
        font-size: 75px !important;       /* <<< increase tab font size */
        padding: 10px 20px !important;     /* <<< optional: more spacing */
        background-color: #222222 !important; 
    }

    /* Hover effect */
    button[data-baseweb="tab"]:hover {
        color: #FFC300 !important; /* Yellow */
    }

    /* 🔴 Remove / override the moving red underline */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;  /* or same as page bg */
        height: 0px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)



# Expander Styling

st.markdown(
        """
    <style>
    .streamlit-expanderHeader {
    #   font-weight: bold;
        background: #e1dee9;
        font-size: 180px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    
custom_css = """
<style>
    .streamlit-tabs-label {
        font-size: 300px;  /* You can adjust the font size as needed */
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
  
##########################################
##  Title, Tabs, and Sidebar            ##
##########################################
#Explore NHL Advanced Stats, Simply
st.title("Check This Data")
st.markdown('''##### <span style="color: #aaaaaa">Explore NHL Advanced Stats, Simply</span>
            ''', unsafe_allow_html=True)
                
tab_standings, tab_txgiving, tab_teams = st.tabs(["Standings","Thanksgiving Predictor", "Teams"])
st.sidebar.markdown("League-Wide Standings")


##########################################
##  Playoff Odds Sidebar                ##
##########################################
@st.cache_data(show_spinner=True)



##########################################
## Standings Tab                        ##
##########################################

def display_standings():
    try:
        standings =  fetch_current_standings()
        return standings
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
    

def load_standings(standings):
    standings['Conference'] = standings['conferenceName']
    standings['Conference Rank'] = standings['conferenceSequence']
    standings['Division'] = standings['divisionName']
    standings['Division Rank'] = standings['divisionSequence']
    standings['Team'] = standings['team_name']
    standings['Games Played'] = standings['gamesPlayed']
    standings['logo'] = standings['teamLogo']  # Assuming this contains the SVG URL
    standings['Win Pct'] = standings['winPctg']
    standings['Points'] = standings['points']
    standings['Points Pct'] = standings['pointPctg']
    standings['Wild Card Rank'] = standings['wildcardSequence']
    # Select specific columns to return
    selected_columns = ['Conference', 'Conference Rank', 'Division', 'Division Rank', 'Team', 'Games Played', 'logo', 'Win Pct', 
                        'Points', 'Points Pct', 'Wild Card Rank']
    league_standings_df = standings[selected_columns]
    return league_standings_df

def todays_standings():
    try:
        standings = display_standings()  # Fetch the data
        if standings is None:
            return  # Exit if no standings were fetched
            
        league_standings_df = load_standings(standings)
        
        # Create league rank using Points → PointsPct (pointPctg)
        league_standings_df = (
            league_standings_df
                .sort_values(['Points', 'Points Pct'], ascending=[False, False])
                .reset_index(drop=True)
        )

        league_standings_df['League Rank'] = league_standings_df.index + 1

        # ---------------------------------------------------------------------
        # 1. Get top 3 teams in each division (automatic qualifiers)
        # ---------------------------------------------------------------------
        #create a wild card view
        playoff_standings_df = load_standings(standings)
        playoff_standings_df = (
            playoff_standings_df
            .sort_values(['Conference', 'Division','Division Rank'], ascending=[False, False, False])
            .reset_index(drop=True)
        )
        
        division_top3 = (
            playoff_standings_df
            .groupby(['Conference', 'Division'])
            .head(3)                 # top 3 per division
            .reset_index(drop=True)
        )

        # ---------------------------------------------------------------------
        # 2. Collect remaining teams (Division Rank >= 4)
        # ---------------------------------------------------------------------
        division_remaining = (
            playoff_standings_df[
                playoff_standings_df['Division Rank'] > 3
            ].copy()
        )

        # ---------------------------------------------------------------------
        # 3. Wild Card Race
        # ---------------------------------------------------------------------
        # wildcardSequence
        wild_card_east = (
            division_remaining[division_remaining['Conference']== 'Eastern']
            .sort_values(['Points', 'Points Pct'], ascending=[False, False])
            .reset_index(drop=True)
        )
        wild_card_east['Wild Card Rank'] = wild_card_east.index + 1
 
        
        wild_card_west = (
            division_remaining[division_remaining['Conference']== 'Western']
            .sort_values(['Points', 'Points Pct'], ascending=[False, False])
            .reset_index(drop=True)
        )
        wild_card_west['Wild Card Rank'] = wild_card_west.index + 1
        
        
        # ---------------------------------------------------------------------
        # 4. Playoffs Race
        # ---------------------------------------------------------------------
        eastern_conference = (
                    league_standings_df[league_standings_df['Conference']== 'Eastern']
                    .sort_values(['Wild Card Rank'])
                    .reset_index(drop=True)
                ).head(8)
        eastern_conference['Wild Card Rank'] = eastern_conference.index + 1
        
        western_conference = (
                    league_standings_df[league_standings_df['Conference']== 'Western']
                    .sort_values(['Wild Card Rank'])
                    .reset_index(drop=True)
                ).head(8)
        western_conference['Wild Card Rank'] = western_conference.index + 1
        
        
        #Define colors for each division
        division_colors = {
            'Atlantic': '#087e8b', 
            'Metropolitan': '#ff5a5f',  
            'Central': '#dcdcdd',  
            'Pacific': '#3c3c3c',  
        }

        # Dropdown for standings selection
        divisions = league_standings_df['Division'].unique().tolist()
        divisions.sort()
        divisions.append("Wild Card Race - East")
        divisions.append("Wild Card Race - West")
        divisions.append("League-Wide")
        divisions.append("Eastern Conference")
        divisions.append("Western Conference")


        # Select division from the sidebar
        selected_division = st.selectbox("Select View:", divisions)
        
        # ------------------------------------------------------------
        # **1. LEAGUE-WIDE VIEW**
        # ------------------------------------------------------------
        if selected_division == "League-Wide":

            # already sorted by Points → Points%
            sorted_df = league_standings_df

            # top 8 per conference
            conference_teams = (
                sorted_df
                .groupby("Conference")
                .head(32)
                .reset_index(drop=True)
            )

            filtered_standings = (
                conference_teams
                .sort_values(['Points', 'Points Pct'], ascending=[False, False])
                .reset_index(drop=True)
            )

            ranking = filtered_standings['League Rank']


        # ------------------------------------------------------------
        # **2. Conference View
        # ------------------------------------------------------------
        elif selected_division == "Eastern Conference":
            
            eastern_conference_view = (
                eastern_conference
                .sort_values([
                    'Wild Card Rank'
                ], ascending=[True])
                .reset_index(drop=True)
            )

            filtered_standings = eastern_conference_view
            ranking = None

        elif selected_division == "Western Conference":
           
            
            western_conference_view = (
                western_conference
                .sort_values([
                    'Wild Card Rank'
                ], ascending=[True])
                .reset_index(drop=True)
            )

            filtered_standings = western_conference_view
            ranking = None
            
        # ------------------------------------------------------------
        # **2. Wild Card East
        # ------------------------------------------------------------
        elif selected_division == "Wild Card Race - East":

            east_playoff_view = (
                wild_card_east
                .sort_values([
                    'Wild Card Rank'
                ], ascending=[True])
                .reset_index(drop=True)
            )

            filtered_standings = east_playoff_view
            ranking = None

        elif selected_division == "Wild Card Race - West":
        # Eastern Conference only
            # west_top3 = division_top3[division_top3['Conference']=='Western']
            

            # west_playoff_view = pd.concat([west_top3, wild_card_west], ignore_index=True)

            west_playoff_view = (
                wild_card_west
                .sort_values([
                    'Wild Card Rank'
                ], ascending=[True])
                .reset_index(drop=True)
            )

            filtered_standings = west_playoff_view
            ranking = None

        # ------------------------------------------------------------
        # **3. DIVISION VIEW**
        # ------------------------------------------------------------
        else:
            filtered_standings = (
                league_standings_df[
                    league_standings_df['Division'] == selected_division
                ]
                .sort_values(['Division Rank'], ascending=[True])
                .reset_index(drop=True)
            )

            ranking = filtered_standings['Division Rank']
        
        def create_dataframe(n):
                div_standings = []

                for index, row in filtered_standings.iterrows():
                        team = row['Team']
                        points = row['Points']
                        division = row['Division']
                        games_played = row['Games Played']
                        logo_url = row['logo']  # SVG logo link
                        div_standings.append(row)

                    # Create DataFrame from the collected data
                return pd.DataFrame(div_standings)

            # Call the function to create the DataFrame
        
        div_standings = create_dataframe(8)
        # #Create visual representation for each team
        team = div_standings['Team']
        points = div_standings['Points']
        division = div_standings['Division']
        logo_url = div_standings['logo']
        games_played = div_standings['Games Played']

        max_points = points.max()
        min_points = points.min()

        # ----- HEIGHT & SPACING SETUP -----
        BASE_HEIGHT = 300          # this will now be the TRUE visible range
        SPACING = 2
        scale_height = BASE_HEIGHT * SPACING
        # Add some padding to top/bottom of the line only (NOT the whole container)
        LINE_EXTRA = 100  # pixels above + below
        html_content = f"""
        <div style="display: flex; flex-direction: column; align-items: flex-start;
                    position: relative; height: {scale_height}px; margin: 40px 0;">

            <div style="
                position: absolute;
                left: 9.7%;
                width: 4px;
                height: {scale_height + LINE_EXTRA}px;
                background: linear-gradient(to bottom,  #d9d9d9, #ffffff,#3c6e71,#284b63, #353535 );
                transform: translateY(-{LINE_EXTRA/2}px);
            "></div>
        """

        # Group teams by point total
        standing_points = {}

        for i, point in enumerate(points):
            logo_url = div_standings['logo'].iloc[i]
            team_name = div_standings['Team'].iloc[i]
            division_name = div_standings['Division'].iloc[i]

            standing_points.setdefault(point, []).append({
                'team': team_name,
                'logo': logo_url,
                'division': division_name,
            })

        # Sort points from high to low
        sorted_standing_points = {
            k: standing_points[k] for k in sorted(standing_points.keys(), reverse=True)
        }

        spread = max(max_points - min_points, 2)
        # Draw each point level
        for point, teams in sorted_standing_points.items():

            # NEW → scale relative to actual standings
            normalized = (point - min_points) / spread
            position = scale_height - (normalized * scale_height)

            # Label left of the line
            html_content += f"""
            <div style="position: absolute; left: 0%; top: {position}px;
                        color: white; font-size: 35px; line-height: 10px;">
                {point}
            </div>

            <div style="position: absolute; left: 12%; top: {position-25}px;
                        display: flex; gap: 5px;">               
        
            """

            # Team logo circles
            for team_info in teams:
                tooltip = f"{team_info['team']} — {team_info['division']} Division"
                html_content += f"""
                <div title="{tooltip}"
                    style="background-color: white;
                            border: 8px solid {division_colors.get(team_info['division'], 'grey')};
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin-left: 10px;">
                    <img src="{team_info['logo']}"
                        alt="{team_info['team']} Logo"
                        width="50" height="50"
                        style="border-radius: 50%;">
                </div>
                """
                
            # # Close logos container
            html_content += "</div>"

            # Dot on the vertical line
            html_content += f"""
            <div style="position: absolute; left: 10%; top: {position}px;
                        width: 10px; height: 10px; background-color: #FFCDB2;
                        border-radius: 50%; transform: translateX(-50%);">
            </div>
            """

        # Close outer container
        html_content += "</div>"
        centered_html = f"""
        <div style="
            width: 100%;
            display: flex;
            justify-content: center;
            margin-top: 20px;
        ">
            <div style="
                position: relative;
                width: 600px;      /* ← adjust — this defines the width of the whole graphic */
            ">
                {html_content}
            </div>
        </div>
        """

        components.html(centered_html, height=scale_height + 150, scrolling=False)



    except Exception as e:
        st.error(f"Error loading standings data: {e}")
        return None


with tab_standings:

    st.subheader("Current Standings")

    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(f"{today}")
    todays_standings()
    
##########################################
## Thanksgiving Tab                     
##########################################
with tab_txgiving:

    cols = st.columns([1, 3])

    @st.cache_data(ttl="6h")
    def load_full_data():
        df = pd.read_csv("predictions_concat.csv")

        # Normalize fields
        df["tri_code"] = df["tri_code"].str.upper().str.strip()
        df["team_name"] = df["team_name"].str.strip()
        df["season"] = df["season_id"].astype(int)
        df["label"] = df["tri_code"]

        return df

    full_df = load_full_data()
    
    # =========================================================
    #  Division Colors
    # =========================================================
    division_colors = {
        "Atlantic": "#087e8b",
        "Metropolitan": "#ff5a5f",
        "Central": "#dcdcdd",
        "Pacific": "#3c3c3c",
        "Unknown": "#808080",
    }

    team_to_division = {
        # Atlantic
        "BOS": "Atlantic", "MTL": "Atlantic", "OTT": "Atlantic", "TOR": "Atlantic",
        "DET": "Atlantic", "BUF": "Atlantic", "TBL": "Atlantic", "FLA": "Atlantic",

        # Metropolitan
        "NYR": "Metropolitan", "NYI": "Metropolitan", "NJD": "Metropolitan",
        "WSH": "Metropolitan", "PIT": "Metropolitan", "PHI": "Metropolitan",
        "CAR": "Metropolitan", "CBJ": "Metropolitan",

        # Central
        "NSH": "Central", "DAL": "Central", "STL": "Central", "CHI": "Central",
        "MIN": "Central", "WPG": "Central", "UTA": "Central", "COL": "Central",

        # Pacific
        "CGY": "Pacific", "EDM": "Pacific", "VAN": "Pacific",
        "SEA": "Pacific", "SJS": "Pacific", "VGK": "Pacific",
        "LAK": "Pacific", "ANA": "Pacific",

        # ARI – not used anymore
        "ARI": "Unknown",
    }

    # =========================================================
    #  Inject JS to tag each multiselect chip with class "tag-XXX"
    # =========================================================
    st.markdown("""
    <script>
    const observer = new MutationObserver(() => {
        document.querySelectorAll('span[data-baseweb="tag"]').forEach(tag => {
            const text = tag.innerText.replace("×","").trim();
            if (text && !tag.classList.contains("tag-" + text)) {
                tag.classList.add("tag-" + text);
            }
        });
    });
    observer.observe(document.body, { subtree: true, childList: true });
    </script>
    """, unsafe_allow_html=True)

    # =========================================================
    #  CSS to color the chips based on division
    # =========================================================
    css_rules = "<style>"

    for team, div in team_to_division.items():
        color = division_colors.get(div, "#808080")
        css_rules += f"""
        .tag-{team} {{
            background-color: {color} !important;
            color: white !important;
            border-radius: 6px !important;
        }}
        """

    css_rules += "</style>"

    st.markdown(css_rules, unsafe_allow_html=True)
    
    # =========================================================
    #  TEAM SELECTION UI
    # =========================================================
    TRI_CODES = sorted(full_df["tri_code"].unique())
    available_labels = ["All Teams"] + sorted(TRI_CODES)

    top_left_cell = cols[0].container(border=True, height="stretch", vertical_alignment="center")

    with top_left_cell:
        st.subheader("Team Selection")

        selected_labels = st.multiselect(
            "Select Teams",
            options=available_labels,
            default=["BOS"],  
        )

        # ---------------------------------------------------
        # Logic for handling "All Teams"
        # ---------------------------------------------------
        
        # If "All Teams" is selected → ignore everything else
        if "All Teams" in selected_labels:
            selected_teams = TRI_CODES[:]   # all teams
        else:
            selected_teams = selected_labels[:]  # individual selections

        # If user clears everything, revert to All Teams
        if not selected_teams:
            selected_teams = TRI_CODES[:]
            st.info("No team selected — showing ALL teams.", icon=":material/info:")


    # =========================================================
    #  SEASON SELECTION — All / Custom / Range
    # =========================================================
    season_map = {
        "2013-14": 20132014,
        "2014-15": 20142015,
        "2015-16": 20152016,
        "2016-17": 20162017,
        "2017-18": 20172018,
        "2018-19": 20182019,
        "2019-20": 20192020,
        "2021-22": 20212022,
        "2022-23": 20222023,
        "2023-24": 20232024,
        "2024-25": 20242025,
        "2025-26": 20252026,
    }
    season_labels = list(season_map.keys())


    with top_left_cell:
        st.subheader("Season Selection")

        season_mode = st.pills(
            "Mode",
            options=["All Seasons", "This Season", "Custom Selection"],
            default="All Seasons",
        )

    # ----------------------------------------------------
    # HANDLE "THIS SEASON"
    # ----------------------------------------------------
    if season_mode == "This Season":
        this_season_label = "2025-26"              # Display label
        selected_seasons = [this_season_label]     # Must be a LIST
        selected_season_ids = [season_map[this_season_label]]
        
        
    # ===============================================
    # CUSTOM SELECTION — MULTI-PICK PILL BUTTONS
    # ===============================================
    if season_mode == "Custom Selection":

        # Initialize session state on first load
        if "selected_custom_seasons" not in st.session_state:
            st.session_state.selected_custom_seasons = []

        st.write("Choose seasons:")

        # Layout pills in rows
        pill_cols = st.columns(3)

        for i, season in enumerate(season_labels):
            col = pill_cols[i % 3]

            # Whether this pill is ON
            active = season in st.session_state.selected_custom_seasons

            # Button label styling
            label = f"✔️ {season}" if active else season

            # Clicking toggles ON/OFF
            if col.button(label, key=f"pill_{season}"):
                if active:
                    st.session_state.selected_custom_seasons.remove(season)
                else:
                    st.session_state.selected_custom_seasons.append(season)

        selected_seasons = st.session_state.selected_custom_seasons[:]

    # ===============================================
    # ALL SEASONS
    # ===============================================
    elif season_mode == "All Seasons":
        selected_seasons = season_labels[:]

    # # =====================================s==========
    # # SLIDER RANGE SELECTION
    # # ===============================================
    # elif season_mode == "Season Range":
    #     start_s, end_s = st.select_slider(
    #         "Season Range",
    #         options=season_labels,
    #         value=(season_labels[0], season_labels[-1])
    #     )
    #     selected_seasons = season_labels[
    #         season_labels.index(start_s) : season_labels.index(end_s) + 1
    #     ]


    # Convert selected season labels → numeric IDs
    selected_season_ids = [season_map[s] for s in selected_seasons]


    # =========================================================
    # FILTER DATA
    # =========================================================
    pred = full_df[full_df["tri_code"].isin(selected_teams)].copy()

    if selected_season_ids:
        pred = pred[pred["season"].isin(selected_season_ids)]

    pred["made_playoffs_label"] = pred["made_playoffs"].map({1: "Yes", 0: "No"}).fillna("TBD")
    pred['playoff_pred_label'] = pred['predicted_status'].map({1: "Yes", 0: "No"})  

    # =========================================================
    # RIGHT PANEL — ALTair Visualization
    # =========================================================
    right_cell = cols[1].container(border=True, height="stretch", vertical_alignment="center")

    team_colors = {
    "ANA": "#F47A38",
    "ARI": "#8C2633",
    "BOS": "#FFB81C",
    "BUF": "#002654",
    "CAR": "#CC0000",
    "CBJ": "#002654",
    "CGY": "#C8102E",
    "CHI": "#CF0A2C",
    "COL": "#6F263D",
    "DAL": "#006847",
    "DET": "#CE1126",
    "EDM": "#FF4C00",
    "FLA": "#B9975B",
    "LAK": "#F7F3F3",
    "MIN": "#154734",
    "MTL": "#AF1E2D",
    "NJD": "#CE1126",
    "NSH": "#FFB81C",
    "NYI": "#00529B",
    "NYR": "#0038A8",
    "OTT": "#DA1A32",
    "PHI": "#F74902",
    "PIT": "#FCB514",
    "SEA": "#99D9D9",
    "SJS": "#006D75",
    "STL": "#002F87",
    "TBL": "#002868",
    "TOR": "#00205B",
    "UTA": "#6F2DA8",
    "VAN": "#00205B",
    "VGK": "#B4975A",
    "WPG": "#041E42",
    "WSH": "#C8102E",
    }


    with right_cell:
        st.subheader("Playoff Probability at Thanksgiving")

        if pred.empty:
            st.warning("No data to plot.")
        else:

            # ---------------------------------------------------------------
            # Build dynamic domain & range for selected teams ONLY
            # ---------------------------------------------------------------
            color_domain = [t for t in pred["tri_code"].unique() if t in team_colors]
            color_range = [team_colors[t] for t in color_domain]

            # ---------------------------------------------------------------
            # 1. SINGLE SEASON → BAR CHART
            # ---------------------------------------------------------------
            if len(selected_season_ids) == 1:
                season_label = selected_seasons[0]

                chart = (
                    alt.Chart(pred)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "tri_code:N",
                            title="Team",
                            sort="-y",
                            axis=alt.Axis(labelAngle=0)
                        ),
                        y=alt.Y(
                            "playoff_prob:Q",
                            title="Probability",
                            scale=alt.Scale(domain=[0, 1])
                        ),
                        color=alt.Color(
                            "tri_code:N",
                            title="Team",
                            scale=alt.Scale(
                                domain=color_domain,
                                range=color_range
                            ),
                            legend=alt.Legend(
                                orient="bottom",
                                direction="horizontal",
                                columns=16,
                                padding=0,            # ← remove extra space
                                titleAnchor="middle",
                                symbolSize=120,
                                labelLimit=600
                            )
                        ),
                        tooltip=[
                            # alt.Tooltip("tri_code", title="Team"),
                            alt.Tooltip("team_name", title="Team"),
                            alt.Tooltip("playoff_prob:Q", title="Probability", format=".1%"),
                            alt.Tooltip("playoff_pred_label:N", title = "Playoff Prediction"),
                            alt.Tooltip("made_playoffs_label:N", title="Made Playoffs"),
                        ],
                    )
                    .properties(
                        title=f"Playoff Probability — {season_label}",
                        height=500                         # ←  chart height
                    )
                    .configure_legend(
                        orient="bottom",
                        padding=0,                         # ← required: removes bottom blank area
                        labelLimit=600,
                        title=None
                    )
                )

                st.altair_chart(chart, use_container_width=True)

            # ---------------------------------------------------------------
            # 2. MULTIPLE SEASONS → LINE CHART
            # ---------------------------------------------------------------

            else:
                chart = (
                    alt.Chart(pred)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X(
                            "season:O",
                            title="Season",
                            sort="ascending",
                            axis=alt.Axis(labelAngle=0)
                        ),
                        y=alt.Y(
                            "playoff_prob:Q",
                            title="Probability",
                            scale=alt.Scale(domain=[0, 1])
                        ),
                        color=alt.Color(
                            "tri_code:N",
                            title="Team",
                            scale=alt.Scale(
                                domain=color_domain,
                                range=color_range
                            ),
                            legend=alt.Legend(
                                orient="bottom",
                                direction="horizontal",
                                columns=16,
                                padding=0,        # ← tighten spacing
                                titleAnchor="middle",
                                symbolSize=120,
                                labelLimit=600
                            )
                        ),
                        tooltip=[
                            # alt.Tooltip("tri_code", title="Team"),
                            alt.Tooltip("team_name", title="Team"),
                            alt.Tooltip("season:O", title="Season"),
                            alt.Tooltip("playoff_prob:Q", title="Probability", format=".1%"),
                            alt.Tooltip("playoff_pred_label:N", title = "Playoff Prediction"),
                            alt.Tooltip("made_playoffs_label:N", title="Made Playoffs"),
                        ],
                    )
                    .properties(height=500)
                    .configure_legend(
                        orient="bottom",
                        padding=0,             # ← eliminates huge bottom gap
                        labelLimit=600,
                        title=None
                    )
                )

                st.altair_chart(chart, use_container_width=True)

    # =========================================================
    # BEST + WORST PLAYOFF PROBABILITY
    # =========================================================
    if not pred.empty:
        prob_map = {row["playoff_prob"]: row["tri_code"] for _, row in pred.iterrows()}

        best_prob, best_team = max(prob_map.items())
        worst_prob, worst_team = min(prob_map.items())

        bottom_left_cell = cols[0].container(border=True, height="stretch", vertical_alignment="center")

        with bottom_left_cell:
            st.subheader("Season Highlights")

            mcols = st.columns(2)

            mcols[0].metric(
                "Best Probability",
                best_team,
                f"{best_prob*100:.1f}%" 
            )

            mcols[1].metric(
                "Worst Probability",
                worst_team,
                 f"{worst_prob*100:.1f}%"
            )


##########################################
## Teams Tab                            ##
##########################################
with tab_teams:
    
    cols = st.columns([1, 3])
    