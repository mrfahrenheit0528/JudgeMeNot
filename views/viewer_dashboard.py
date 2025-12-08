import flet as ft
import threading
import time
# IMPORT BOTH SERVICES
from services.quiz_service import QuizService
from services.pageant_service import PageantService
from core.database import SessionLocal
from models.all_models import Event, Segment, Score, Contestant, Criteria
from sqlalchemy import func

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
        print(f"DEBUG: Back Button Clicked. Session Role: '{user_role}'") 
        
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
                ft.Icon(icon, size=40, color="white70"),
                ft.Text(event_data.name, size=18, weight="bold", color="white", text_align="center", no_wrap=False, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(
                    content=ft.Text("View Standings", size=12, color="white"),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.BLUE_600,
                    border_radius=20
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=ft.Colors.WHITE10,
            border_radius=15,
            padding=20,
            width=200,
            height=200,
            ink=True,
            on_click=lambda e: page.go(f"/leaderboard/{event_data.id}"),
            border=ft.border.all(1, ft.Colors.WHITE10),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
        )

    header = ft.Column([
        ft.Text("Event Gallery", size=32, weight="bold", color="white"),
        ft.Text("Select an event to view live results", size=16, color="white70")
    ])

    grid = ft.GridView(
        expand=True,
        runs_count=5,
        max_extent=250,
        child_aspect_ratio=1.0,
        spacing=20,
        run_spacing=20,
    )

    if not events:
        grid.controls.append(ft.Text("No events found.", color="white70"))
    else:
        for e in events:
            grid.controls.append(create_event_card(e))

    return ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.BLUE_900, ft.Colors.PURPLE_900]
        ),
        padding=30,
        content=ft.Column([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", tooltip="Go Back", on_click=go_back_logic),
                header
            ], spacing=20),
            ft.Divider(color="white24", height=30),
            grid
        ])
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
    
    # UI Elements
    title_text = ft.Text("Loading...", size=30, weight="bold", color="white")
    status_text = ft.Text("Waiting for updates...", color="white70", size=14)
    content_wrapper = ft.Column(expand=True, scroll="adaptive")

    def get_data():
        db = SessionLocal()
        event = db.query(Event).get(event_id)
        if event:
            title_text.value = event.name
        
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
                    # For Quiz Bee, we decided all are revealed, so always append
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
                    
                    # Accumulate Weighted Total
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
                content_wrapper.controls.append(ft.Text("No scores available yet.", color="white"))
                page.update()
                return

            if event_type == "QuizBee":
                # --- QUIZ BEE TABLE ---
                cols = [ft.DataColumn(ft.Text("Rank", weight="bold", color="white")), ft.DataColumn(ft.Text("Name", weight="bold", color="white"))]
                
                # 1. Non-Final Rounds
                for h in p_headers: cols.append(ft.DataColumn(ft.Text(h, size=12, color="white70"), numeric=True))
                
                # 2. Total (If all non-finals shown)
                if show_p_total: cols.append(ft.DataColumn(ft.Text("PRELIM TOTAL", weight="bold", color="cyan"), numeric=True))
                
                # 3. Final Rounds
                for h in f_headers: cols.append(ft.DataColumn(ft.Text(h, size=12, color="orange"), numeric=True))
                
                # 4. Final Total (REMOVED as requested)
                # cols.append(ft.DataColumn(ft.Text("FINAL TOTAL", ...))) 

                rows = []
                for i, r in enumerate(results):
                    is_elim = "Eliminated" in r['name']
                    txt_col = ft.Colors.GREY if is_elim else ft.Colors.WHITE
                    
                    cells = [ft.DataCell(ft.Text(str(i+1), color=txt_col)), ft.DataCell(ft.Text(r['name'], color=txt_col, weight="bold"))]
                    for s in r['p_bd']: cells.append(ft.DataCell(ft.Text(str(s), color=txt_col)))
                    if show_p_total: cells.append(ft.DataCell(ft.Text(str(r['p_tot']), weight="bold", color=ft.Colors.CYAN if not is_elim else ft.Colors.GREY)))
                    for s in r['f_bd']: cells.append(ft.DataCell(ft.Text(str(s), color=txt_col)))
                    
                    # NOTE: We removed the Final Total column, but the data (f_tot) is still calculated for sorting.
                    
                    rows.append(ft.DataRow(cells=cells))

                content_wrapper.controls.append(ft.Container(content=ft.DataTable(columns=cols, rows=rows, border=ft.border.all(1, "white10"), heading_row_color="white10"), padding=10))

            else:
                # --- PAGEANT TABLE (Split by Gender) ---
                def build_gender_table(gender, color_theme):
                    subset = [r for r in results if r.get('gender') == gender]
                    if not subset: return None
                    
                    # Resort subset based on current ranking criteria
                    if f_headers: subset.sort(key=lambda x: x['f_tot'], reverse=True)
                    else: subset.sort(key=lambda x: x['p_tot'], reverse=True)

                    for idx, s in enumerate(subset): s['rank'] = idx + 1

                    # --- COLUMNS ---
                    cols = [
                        ft.DataColumn(ft.Text("Rank", weight="bold", color="white")), 
                        ft.DataColumn(ft.Text(f"{gender.upper()} CANDIDATE", weight="bold", color=color_theme))
                    ]
                    # 1. Non-Final Rounds
                    for h in p_headers: 
                        cols.append(ft.DataColumn(ft.Text(h, size=12, color="white70"), numeric=True))
                    
                    # 2. Total (If all non-finals shown)
                    if show_p_total:
                        cols.append(ft.DataColumn(ft.Text("PRELIM TOTAL", weight="bold", color="cyan"), numeric=True))

                    # 3. Final Rounds
                    for h in f_headers:
                        cols.append(ft.DataColumn(ft.Text(h, size=12, color="orange"), numeric=True))

                    # 4. Final Total (REMOVED as requested)

                    rows = []
                    for r in subset:
                        cells = [
                            ft.DataCell(ft.Text(str(r['rank']), color="white")),
                            ft.DataCell(ft.Text(r['name'], weight="bold", color="white"))
                        ]
                        
                        # Prelim Segments
                        for s_val in r['segment_scores']:
                            cells.append(ft.DataCell(ft.Text(str(s_val), color="white70")))
                        
                        # Prelim Total
                        if show_p_total:
                            cells.append(ft.DataCell(ft.Text(f"{r['p_tot']}%", weight="bold", color="cyan")))

                        # Final Segments
                        for s_val in r['final_scores']:
                            cells.append(ft.DataCell(ft.Text(str(s_val), color="white", weight="bold")))

                        rows.append(ft.DataRow(cells))
                    
                    return ft.DataTable(columns=cols, rows=rows, border=ft.border.all(1, "white10"), heading_row_color="white10", column_spacing=20)

                # Build Tables
                male_table = build_gender_table("Male", "blue")
                female_table = build_gender_table("Female", "pink")

                if male_table:
                    content_wrapper.controls.extend([ft.Text("MALE CATEGORY", weight="bold", color="blue", size=20), male_table, ft.Container(height=30)])
                if female_table:
                    content_wrapper.controls.extend([ft.Text("FEMALE CATEGORY", weight="bold", color="pink", size=20), female_table])

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

    return ft.Container(
        expand=True,
        gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[ft.Colors.BLUE_900, ft.Colors.PURPLE_900]),
        padding=20,
        content=ft.Column([
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back, icon_color="white"), ft.Column([title_text, status_text], spacing=0)]),
            ft.Divider(color="white24"),
            content_wrapper
        ])
    )