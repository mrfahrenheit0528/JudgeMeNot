import flet as ft
import threading
import time
from services.quiz_service import QuizService
from services.pageant_service import PageantService
from core.database import SessionLocal
from models.all_models import Event, Segment, Score, Contestant, Criteria
from sqlalchemy import func
from components.dialogs import show_about_dialog, show_contact_dialog # reused for header

# ---------------------------------------------------------
# VIEW 1: EVENT GALLERY (List of All Events)
# ---------------------------------------------------------
def EventListView(page: ft.Page):
    
    # 1. Fetch All Events
    db = SessionLocal()
    events = db.query(Event).all()
    db.close()

    # --- SMART NAVIGATION LOGIC ---
    def go_back_logic(e):
        user_role = page.session.get("user_role")
        if user_role in ["Admin", "AdminViewer"]:
            page.go("/admin")
        elif user_role == "Judge":
            page.go("/judge")
        elif user_role == "Tabulator":
            page.go("/tabulator")
        else:
            page.go("/login")

    def create_event_card(event_data):
        icon = ft.Icons.WOMAN if event_data.event_type == "Pageant" else ft.Icons.LIGHTBULB
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color="white"), 
                ft.Text(event_data.name, size=16, weight="bold", color="white", text_align="center", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(
                    content=ft.Text("View Results", size=12, color="white", weight="bold"),
                    padding=ft.padding.symmetric(horizontal=15, vertical=8),
                    bgcolor=ft.Colors.with_opacity(0.3, "white"), # Glass effect button
                    border_radius=20,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=ft.Colors.with_opacity(0.1, "white"), # Glass card
            border_radius=15,
            padding=20,
            width=180,
            height=180,
            ink=True,
            on_click=lambda e: page.go(f"/leaderboard/{event_data.id}"),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "white")),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK45)
        )

    # Standard Header (Consistent with App)
    header_logo = ft.Container(
        width=40, height=40, border_radius=50, bgcolor="transparent",
        border=ft.border.all(2, "black"), padding=5,
        content=ft.Image(src="hammer.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.GAVEL, color="black"))
    )

    header = ft.Container(
        height=70, padding=ft.padding.symmetric(horizontal=20), bgcolor="#80C1FF", 
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_900), # Darker shadow for depth
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_color="black", on_click=go_back_logic),
                    header_logo, 
                    ft.Text("Event Gallery", size=20, weight="bold", color="black")
                ]),
                ft.Row(spacing=5, controls=[
                    ft.TextButton("ABOUT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_about_dialog(page)),
                    # FIXED: Added Contact Button back
                    ft.TextButton("CONTACT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_contact_dialog(page)),
                ])
            ]
        )
    )

    # Using Row with wrap=True + alignment=center ensures items are centered even if few
    events_row = ft.Row(
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=30,
        run_spacing=30,
        controls=[]
    )

    if not events:
        events_row.controls.append(ft.Text("No events found.", color="white70"))
    else:
        for e in events:
            events_row.controls.append(create_event_card(e))

    return ft.Container(
        expand=True,
        # THE PURPLE GRADIENT BACKGROUND
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#831CA5", "#074E96"] # Deep Purple to Light
        ),
        content=ft.Column(
            expand=True,
            controls=[
                header,
                ft.Container(
                    content=ft.Column(
                        controls=[events_row],
                        scroll="adaptive", # Allow vertical scroll for many events
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER # Ensure content centers
                    ),
                    padding=30,
                    expand=True,
                    alignment=ft.alignment.center # Center the whole block
                )
            ]
        )
    )

# ---------------------------------------------------------
# VIEW 2: SPECIFIC EVENT LEADERBOARD
# ---------------------------------------------------------
def EventLeaderboardView(page: ft.Page, event_id: int):
    # Services
    quiz_service = QuizService()
    pageant_service = PageantService()

    # State
    is_active = True
    event_type = "Pageant" 
    
    db = SessionLocal()
    ev = db.query(Event).get(event_id)
    if ev: event_type = ev.event_type
    db.close()
    
    # UI Elements (White Text for Purple Background)
    title_text = ft.Text("Loading...", size=24, weight="bold", color="white")
    status_text = ft.Text("Waiting for updates...", color="white70", size=14)
    
    # FIXED: Added horizontal_alignment=CENTER to center the tables
    content_wrapper = ft.Column(
        expand=True, 
        scroll="adaptive", 
        spacing=30, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    def get_data():
        db = SessionLocal()
        event = db.query(Event).get(event_id)
        if event:
            title_text.value = event.name.upper()
        
        scores = []
        mode_label = "LIVE RESULTS"
        
        # Headers containers
        p_headers = [] # Prelim headers (Revealed)
        f_headers = [] # Final headers (Revealed)
        
        # Flags
        show_prelim_total = False

        # -------------------------------------------------------------
        # SHARED SEGMENT PROCESSING (For both Quiz & Pageant)
        # -------------------------------------------------------------
        # 1. Fetch Segments
        all_segments = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
        
        prelim_segs = []
        final_segs = []
        seg_map = {s.id: s for s in all_segments}
        
        for seg in all_segments:
            is_final = seg.is_final
            if not is_final and seg.related_segment_id:
                parent = seg_map.get(seg.related_segment_id)
                if parent and parent.is_final: is_final = True
            
            if is_final: final_segs.append(seg)
            else: prelim_segs.append(seg)
        
        # Determine Headers based on Visibility
        if event_type == "QuizBee":
            # AUTO-SHOW ALL FOR QUIZ BEE
            revealed_prelims = prelim_segs
            revealed_finals = final_segs
        else:
            # Respect Admin Toggle for Pageants
            revealed_prelims = [s for s in prelim_segs if s.is_revealed]
            revealed_finals = [s for s in final_segs if s.is_revealed]
        
        p_headers = [s.name for s in revealed_prelims]
        f_headers = [s.name for s in revealed_finals]
        
        # Logic: Show Prelim Total ONLY if ALL prelim segments are revealed
        # For Quiz Bee, this is effectively always True if there are prelims
        if prelim_segs:
            show_prelim_total = (len(revealed_prelims) == len(prelim_segs))
        else:
            show_prelim_total = False

        # Ranking Mode: If ANY final round is shown, rank by Final Score.
        rank_by_final = (len(revealed_finals) > 0)

        # =================================================================
        # QUIZ BEE LOGIC
        # =================================================================
        if event_type == "QuizBee":
            contestants = db.query(Contestant).filter(Contestant.event_id == event_id).all()
            for c in contestants:
                prelim_total = 0; final_total = 0
                p_breakdown = []; f_breakdown = []
                
                # Sum Prelims (Calculate ALL, but only store Revealed for breakdown)
                for seg in prelim_segs:
                    val = db.query(func.sum(Score.score_value)).filter(Score.contestant_id==c.id, Score.segment_id==seg.id).scalar() or 0
                    prelim_total += val
                    p_breakdown.append(int(val))
                
                # Sum Finals
                for seg in final_segs:
                    val = db.query(func.sum(Score.score_value)).filter(Score.contestant_id==c.id, Score.segment_id==seg.id).scalar() or 0
                    final_total += val
                    f_breakdown.append(int(val))
                
                dname = c.name + (" (Eliminated)" if c.status == "Eliminated" else "")
                scores.append({
                    "name": dname,
                    "p_bd": p_breakdown, 
                    "f_bd": f_breakdown,
                    "p_tot": int(prelim_total), 
                    "f_tot": int(final_total),
                    "status": c.status
                })
            
            # Sort
            if rank_by_final: scores.sort(key=lambda x: (x['f_tot'], x['p_tot']), reverse=True)
            else: scores.sort(key=lambda x: x['p_tot'], reverse=True)

        # =================================================================
        # PAGEANT LOGIC
        # =================================================================
        else:
            mode_label = "OFFICIAL RANKINGS"
            
            # Calculate Scores
            contestants = db.query(Contestant).filter(Contestant.event_id == event_id).all()
            
            for c in contestants:
                prelim_row_scores = []
                final_row_scores = []
                
                prelim_weighted_total = 0.0
                final_weighted_total = 0.0
                
                # --- CALCULATE PRELIMS ---
                for seg in prelim_segs:
                    # Calculate segment score (Raw)
                    criterias = db.query(Criteria).filter(Criteria.segment_id == seg.id).all()
                    seg_raw_score = 0.0
                    for crit in criterias:
                        avg_val = db.query(func.avg(Score.score_value)).filter(Score.contestant_id == c.id, Score.criteria_id == crit.id).scalar() or 0.0
                        seg_raw_score += (avg_val * crit.weight)
                    
                    prelim_weighted_total += (seg_raw_score * seg.percentage_weight)
                    
                    if seg.is_revealed:
                        prelim_row_scores.append(round(seg_raw_score, 2))

                # --- CALCULATE FINALS ---
                for seg in final_segs:
                    criterias = db.query(Criteria).filter(Criteria.segment_id == seg.id).all()
                    seg_raw_score = 0.0
                    for crit in criterias:
                        avg_val = db.query(func.avg(Score.score_value)).filter(Score.contestant_id == c.id, Score.criteria_id == crit.id).scalar() or 0.0
                        seg_raw_score += (avg_val * crit.weight)
                    
                    final_weighted_total += seg_raw_score
                    
                    if seg.is_revealed:
                        final_row_scores.append(round(seg_raw_score, 2))

                # --- NORMALIZE PERCENTAGE ---
                prelim_percent = round((prelim_weighted_total / 10.0) * 100, 2)
                final_percent = round((final_weighted_total / 10.0) * 100, 2) 

                scores.append({
                    "name": c.name,
                    "gender": c.gender,
                    "segment_scores": prelim_row_scores,
                    "final_scores": final_row_scores,
                    "p_tot": prelim_percent,
                    "f_tot": final_percent
                })
            
            # Sort
            if rank_by_final: scores.sort(key=lambda x: x['f_tot'], reverse=True)
            else: scores.sort(key=lambda x: x['p_tot'], reverse=True)

        db.close()
        return scores, mode_label, p_headers, f_headers, show_prelim_total

    def refresh_leaderboard():
        try:
            results, mode, p_headers, f_headers, show_p_total = get_data()
            status_text.value = f"{mode} • Live Updates"
            content_wrapper.controls.clear()

            if not results:
                content_wrapper.controls.append(ft.Text("No scores available yet.", color="white70"))
                page.update()
                return

            # --- RESPONSIVE SETTINGS ---
            # 1. Detect screen size (fallback to 400 if not ready)
            current_width = page.width if page.width > 0 else 400
            is_mobile = current_width < 750
            
            # 2. Dynamic Text Sizes
            heading_size = 10 if is_mobile else 12
            data_size = 10 if is_mobile else 12
            badge_size = 20 if is_mobile else 30
            row_height = 40 if is_mobile else 50 # Compact rows on mobile

            def create_modern_table(rows, cols, color_theme, title):
                # The "Card" container for the table
                return ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(title, weight="bold", color="white", size=18 if not is_mobile else 16),
                            padding=ft.padding.symmetric(horizontal=15, vertical=10),
                            bgcolor=color_theme, # Header bar for the card
                            border_radius=ft.border_radius.only(top_left=10, top_right=10)
                        ),
                        ft.Row([
                            ft.DataTable(
                                columns=cols,
                                rows=rows,
                                heading_row_height=row_height,
                                data_row_max_height=row_height + 10, # Slight buffer
                                heading_text_style=ft.TextStyle(weight="bold", color="black", size=heading_size),
                                data_text_style=ft.TextStyle(size=data_size, color="black"),
                                column_spacing=10 if is_mobile else 20, # Tighter spacing on phone
                                # Table styling
                                vertical_lines=ft.border.BorderSide(1, "#F0F0F0"),
                                heading_row_color=ft.Colors.with_opacity(0.1, color_theme), # Subtle tint matching category
                            )
                        ], scroll="adaptive", expand=True) # Horizontal Scroll for mobile
                    ]),
                    bgcolor="white",
                    border_radius=10,
                    padding=0,
                    margin=ft.margin.only(bottom=20),
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK26),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    # RESPONSIVE WIDTH: Auto (None) allows it to shrink to fit content
                    # But we wrap content columns in a Center aligned wrapper to keep it neat
                    width=None 
                )

            if event_type == "QuizBee":
                # --- QUIZ BEE TABLE ---
                cols = [
                    ft.DataColumn(ft.Text("Rank")), 
                    ft.DataColumn(ft.Text("Name"))
                ]
                
                for h in p_headers: cols.append(ft.DataColumn(ft.Text(h, size=heading_size), numeric=True))
                if show_p_total: cols.append(ft.DataColumn(ft.Text("PRELIM TOTAL", weight="bold", size=heading_size), numeric=True))
                for h in f_headers: cols.append(ft.DataColumn(ft.Text(h, size=heading_size), numeric=True))
                
                rows = []
                for i, r in enumerate(results):
                    is_elim = "Eliminated" in r['name']
                    
                    # Modern Rank Badge
                    rank_content = ft.Text(str(i+1), weight="bold", size=data_size)
                    if i == 0: rank_content = ft.Container(content=ft.Text("1", color="white", weight="bold", size=data_size), bgcolor="#FFD700", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center) # Gold
                    elif i == 1: rank_content = ft.Container(content=ft.Text("2", color="white", weight="bold", size=data_size), bgcolor="#C0C0C0", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center) # Silver
                    elif i == 2: rank_content = ft.Container(content=ft.Text("3", color="white", weight="bold", size=data_size), bgcolor="#CD7F32", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center) # Bronze
                    
                    row_color = "#F9FAFB" if i % 2 == 0 else "white" # Very subtle striping
                    text_col = "grey" if is_elim else "black"

                    cells = [
                        ft.DataCell(rank_content), 
                        ft.DataCell(ft.Text(r['name'], color=text_col, weight="bold"))
                    ]
                    for s in r['p_bd']: cells.append(ft.DataCell(ft.Text(str(s), color=text_col)))
                    if show_p_total: cells.append(ft.DataCell(ft.Text(str(r['p_tot']), weight="bold", color="#64AEFF" if not is_elim else "grey")))
                    for s in r['f_bd']: cells.append(ft.DataCell(ft.Text(str(s), color=text_col)))
                    
                    rows.append(ft.DataRow(cells=cells, color=row_color))

                content_wrapper.controls.append(create_modern_table(rows, cols, "#64AEFF", "Quiz Standings"))

            else:
                # --- PAGEANT TABLE (Split by Gender) ---
                def build_gender_table(gender, color_code):
                    subset = [r for r in results if r.get('gender') == gender]
                    if not subset: return None
                    
                    if f_headers: subset.sort(key=lambda x: x['f_tot'], reverse=True)
                    else: subset.sort(key=lambda x: x['p_tot'], reverse=True)

                    # --- COLUMNS ---
                    cols = [
                        ft.DataColumn(ft.Text("Rank")), 
                        ft.DataColumn(ft.Text(f"{gender.upper()} CANDIDATE"))
                    ]
                    for h in p_headers: cols.append(ft.DataColumn(ft.Text(h, size=heading_size), numeric=True))
                    if show_p_total: cols.append(ft.DataColumn(ft.Text("PRELIM %", weight="bold", size=heading_size), numeric=True))
                    for h in f_headers: cols.append(ft.DataColumn(ft.Text(h, size=heading_size), numeric=True))

                    rows = []
                    for idx, r in enumerate(subset):
                        # Modern Rank Badge
                        rank_content = ft.Text(str(idx+1), weight="bold", size=data_size)
                        if idx == 0: rank_content = ft.Container(content=ft.Text("1", color="white", weight="bold", size=data_size), bgcolor="#FFD700", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center)
                        elif idx == 1: rank_content = ft.Container(content=ft.Text("2", color="white", weight="bold", size=data_size), bgcolor="#C0C0C0", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center)
                        elif idx == 2: rank_content = ft.Container(content=ft.Text("3", color="white", weight="bold", size=data_size), bgcolor="#CD7F32", border_radius=50, width=badge_size, height=badge_size, alignment=ft.alignment.center)

                        row_color = "#F9FAFB" if idx % 2 == 0 else "white"

                        cells = [
                            ft.DataCell(rank_content),
                            ft.DataCell(ft.Text(r['name'], weight="bold", color="black"))
                        ]
                        
                        for s_val in r['segment_scores']: cells.append(ft.DataCell(ft.Text(str(s_val))))
                        if show_p_total: cells.append(ft.DataCell(ft.Text(f"{r['p_tot']}%", weight="bold", color="#64AEFF")))
                        for s_val in r['final_scores']: cells.append(ft.DataCell(ft.Text(str(s_val), color="black", weight="bold")))

                        rows.append(ft.DataRow(cells=cells, color=row_color))
                    
                    return create_modern_table(rows, cols, color_code, f"{gender} Category")

                # Build Tables
                male_table = build_gender_table("Male", "#64AEFF") # Login Blue
                female_table = build_gender_table("Female", "#FF64AE") # Pink

                if male_table: content_wrapper.controls.append(male_table)
                if female_table: content_wrapper.controls.append(female_table)

            page.update()
        except Exception as e:
            print(f"ERROR in Leaderboard: {e}") 

    def poll_updates():
        while is_active:
            refresh_leaderboard()
            time.sleep(3)

    threading.Thread(target=poll_updates, daemon=True).start()

    def go_back(e):
        nonlocal is_active; is_active = False 
        page.go("/leaderboard")

    # Header for the specific event view
    # Uses transparent background to blend with the purple gradient
    header = ft.Container(
        height=70, padding=ft.padding.symmetric(horizontal=20),
        content=ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back, icon_color="white"), 
                ft.Column([title_text, status_text], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
            ]
        )
    )

    return ft.Container(
        expand=True,
        # THE PURPLE GRADIENT (Restored & Enhanced)
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#D76750", "#DFCC6B"]
        ),
        content=ft.Column(
            expand=True,
            controls=[
                header,
                ft.Container(
                    content=content_wrapper,
                    padding=20, 
                    expand=True,
                    alignment=ft.alignment.center # Ensures the table column is centered
                )
            ]
        )
    )